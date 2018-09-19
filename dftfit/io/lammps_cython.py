import math
import itertools
import functools
import multiprocessing
import asyncio
import uuid

import numpy as np
import pymatgen as pmg

import lammps
from lammps.potential import (
    write_table_pair_potential,
    write_tersoff_potential,
    write_stillinger_weber_potential,
    write_gao_weber_potential,
    write_vashishta_potential,
    write_comb_potential,
    write_comb_3_potential
)

from ..potential import Potential
from .base import DFTFITCalculator, MDCalculator, MDReader


class LammpsCythonWorker:
    """A lammps cython worker

    All input and output is fully serializable.
    """
    def __init__(self, structures, elements, potential_schema, unique_id=1):
        self.structures = structures
        self.elements = elements
        self.potential = Potential(potential_schema)
        self.unique_id = unique_id
        self.lammps_systems = []

    def _initialize_lammps(self, structure):
        lmp = lammps.Lammps(units='metal', style='full', args=[
            '-log', 'none', '-screen', 'none'
        ])
        lmp.system.add_pymatgen_structure(structure, self.elements)
        lmp.thermo.add('my_ke', 'ke', 'all')
        return lmp

    def create(self):
        for structure in self.structures:
            self.lammps_systems.append(self._initialize_lammps(structure))

    def _apply_potential(self, potential):
        lammps_commands = write_potential(potential, elements=self.elements, unique_id=self.unique_id)
        for command in lammps_commands:
            for lmp in self.lammps_systems:
                lmp.command(command)

    def worker_multiprocessing_loop(self, pipe):
        while True:
            message = pipe.recv()
            if isinstance(message, str) and message == 'quit':
                break
            results = self.compute(message)
            pipe.send(results)
        pipe.close()

    def compute(self, parameters):
        self.potential.optimization_parameters = parameters
        self._apply_potential(self.potential)
        results = []
        for lmp in self.lammps_systems:
            lmp.run(0)
            S = lmp.thermo.computes['thermo_press'].vector
            results.append({
                'forces': lmp.system.forces.copy(),
                'energy': lmp.thermo.computes['thermo_pe'].scalar + lmp.thermo.computes['my_ke'].scalar,
                'stress': np.array([
                    [S[0], S[3], S[5]],
                    [S[3], S[1], S[4]],
                    [S[5], S[4], S[2]]
                ])
            })
        return results


class LammpsCythonDFTFITCalculator(DFTFITCalculator):
    """This is not a general purpose lammps calculator. Only for dftfit
    evaluations. For now there are not plans to generalize it.
    """
    def __init__(self, structures, potential, num_workers=1):
        self.unique_id = str(uuid.uuid1())
        self.structures = structures

        # ensure element indexes are the same between all lammps calculations
        self.elements = set()
        for structure in self.structures:
            self.elements = self.elements | set(structure.species)
        self.elements = list(self.elements)

        self.workers = []
        potential_schema = potential.as_dict()
        if num_workers == 1:
            self.workers.append(LammpsCythonWorker(structures, self.elements, potential_schema, self.unique_id))
        else:
            def create_worker(structures, elements, potential_schema, pipe):
                worker = LammpsCythonWorker(structures, elements, potential_schema, self.unique_id)
                worker.create()
                worker.worker_multiprocessing_loop(pipe)

            self.workers = []
            structure_index = 0
            rem = len(structures) % num_workers
            n = math.floor(len(structures) / num_workers)
            for i in range(num_workers):
                p_conn, c_conn = multiprocessing.Pipe()
                # hand out remaining to first rem < i
                if num_workers - rem >= i:
                    subset_structures = structures[structure_index: structure_index+n+1]
                    structure_index += n + 1
                else:
                    subset_structures = structures[structure_index: structure_index+n]
                    structure_index += n
                p = multiprocessing.Process(target=create_worker, args=(subset_structures, self.elements, potential_schema, c_conn))
                p.start()
                self.workers.append((p, p_conn))

    async def create(self):
        # otherwise seperate process calls this method
        if len(self.workers) == 1:
            self.workers[0].create()

    def _apply_potential_files(self, potential):
        lammps_files = write_potential_files(potential, elements=self.elements, unique_id=self.unique_id)
        for filename, content in lammps_files.items():
            with open(filename, 'w') as f:
                f.write(content)

    async def submit(self, potential, properties=None):
        properties = properties or {'stress', 'energy', 'forces'}
        parameters = potential.optimization_parameters
        self._apply_potential_files(potential)

        results = []
        if len(self.workers) == 1:
            results = self.workers[0].compute(parameters)
        else:
            # send potential to each worker
            for p, p_conn in self.workers:
                p_conn.send(parameters)

            # recv calculation results from each worker
            for p, p_conn in self.workers:
                results.extend(p_conn.recv())

        md_readers = []
        for structure, result in zip(self.structures, results):
            md_readers.append(MDReader(energy=result['energy'], forces=result['forces'], stress=result['stress'], structure=structure))
        return md_readers

    def shutdown(self):
        # nothing is needed if not using multiprocessing module
        if len(self.workers) > 1:
            for p, p_conn in self.workers:
                p_conn.send('quit')
                p.join()


class LammpsCythonMDCalculator(MDCalculator):
    def __init__(self, num_workers=1):
        self.unique_id = str(uuid.uuid1())
        if num_workers != 1:
            raise NotImplementedError('lammps-cython md calculator can only run with one worker')

    async def create(self):
        pass

    async def submit(self, structure, potential, properties=None, lammps_additional_commands=None):
        properties = properties or {'stress', 'energy', 'forces'}
        results = {}

        lammps_additional_commands = lammps_additional_commands or ['run 0']
        lmp = lammps.Lammps(units='metal', style='full', args=[
            '-log', 'none', '-screen', 'none'
        ])
        elements, rotation_matrix = lmp.system.add_pymatgen_structure(structure)
        inv_rotation_matrix = np.linalg.inv(rotation_matrix)
        lmp.thermo.add('my_ke', 'ke', 'all')
        if 'initial_positions' in properties:
            results['initial_positions'] = np.dot(lmp.system.positions.copy(), inv_rotation_matrix)

        lammps_files = write_potential_files(potential, elements=elements, unique_id=self.unique_id)
        for filename, content in lammps_files.items():
            with open(filename, 'w') as f:
                f.write(content)

        lammps_commands = write_potential(potential, elements=elements, unique_id=self.unique_id)
        for command in lammps_commands:
            lmp.command(command)

        for command in lammps_additional_commands:
            lmp.command(command)

        # to handle non-orthogonal unit cells
        if 'lattice' in properties:
            lengths, angles_r = lmp.box.lengths_angles
            angles = [math.degrees(_) for _ in angles_r]
            results['lattice'] = pmg.Lattice.from_parameters(*lengths, *angles).matrix

        if 'positions' in properties:
            results['positions'] = np.dot(lmp.system.positions.copy(), inv_rotation_matrix)

        if 'stress' in properties:
            S = lmp.thermo.computes['thermo_press'].vector
            results['stress'] = np.array([
                [S[0], S[3], S[5]],
                [S[3], S[1], S[4]],
                [S[5], S[4], S[2]]
            ])

        if 'energy' in properties:
            results['energy'] = lmp.thermo.computes['thermo_pe'].scalar + lmp.thermo.computes['my_ke'].scalar

        if 'forces' in properties:
            results['forces'] = lmp.system.forces.copy()

        if 'symbols' in properties:
            results['symbols'] = [elements[i-1] for i in lmp.system.types[0]]

        if 'velocities' in properties:
            results['velocities'] = np.dot(lmp.system.velocities.copy(), inv_rotation_matrix)

        if 'timesteps' in properties:
            results['timesteps'] = lmp.time_step

        # compatibility...
        future = asyncio.Future()
        future.set_result({'results': results})
        return future


def vashishta_mixed_to_vashishta(element_parameters, override_parameters):
    """ Vashishta mixing potential

    Using tersoff for two body mixing rules.
    """
    def mixing_params_from_singles(e1, e2):
        p1 = [float(_) for _ in element_parameters[e1]]
        p2 = [float(_) for _ in element_parameters[e2]]
        # 13 inputs: 14 paramters
        # H (*), eta (1), Zi (1), Zj (1), lambda1 (+), D (*), lambda4 (+), W (*)
        # cuttoff: rc (1), r0 (1)
        # B (1), gamma (1), C (1), costheta0 (1)
        return [
            math.sqrt(p1[0] * p2[0]),            # H
            p1[1],                               # eta
            p1[2],                               # Zi
            p2[2],                               # Zj
            (p1[3] + p2[3]) / 2.0,               # lambda 1
            math.sqrt(p1[4] * p2[4]),            # D
            (p1[5] + p2[5]) / 2.0,               # lambda4
            math.sqrt(p1[6] * p2[6]),            # W
            p1[7],                               # r_cutoff (2)
            p1[8],                               # B
            p1[9],                               # gamma
            p1[10],                              # r_0 (3)
            p1[11],                              # C
            p1[12],                              # costheta0
        ]

    parameters = {}
    for e1, e2, e3 in itertools.product(element_parameters, repeat=3):
        mixing_parameters = mixing_params_from_singles(e1, e2)
        if (e1, e2, e3) in override_parameters:
            parameters[(e1, e2, e3)] = [float(p2) if p2 else p1 for p1, p2 in zip(mixing_parameters, override_parameters)]
        else:
            parameters[(e1, e2, e3)] = mixing_parameters
    return parameters


def tersoff_2_to_tersoff(element_parameters, mixing_parameters):
    def mixing_params_from_singles(e1, e2, mixing_value):
        p1 = [float(_) for _ in element_parameters[e1]]
        p2 = [float(_) for _ in element_parameters[e2]]
        mixing = float(mixing_value)
        return [
            3.0,                                # m
            1.0,                                # gamma
            0.0,                                # lambda3
            p1[0],                              # c
            p1[1],                              # d
            p1[2],                              # costheta0
            p1[3],                              # n
            p1[4],                              # beta
            (p1[5] + p2[5]) / 2,                # lambda2
            mixing * math.sqrt(p1[6] * p2[6]),  # B
            math.sqrt(p1[7] * p2[7]),           # R
            math.sqrt(p1[8] * p2[8]),           # D
            (p1[9] + p2[9]) / 2,                # lambda1
            math.sqrt(p1[10] * p2[10]),         # A
        ]

    parameters = {}
    for e1, e2, e3 in itertools.product(element_parameters, repeat=3):
        if e1 == e2:
            mixing_value = 1.0
        else:
            sorted_e1_e2 = tuple(sorted([e1, e2]))
            mixing_value = mixing_parameters.get(sorted_e1_e2)
            if mixing_value is None:
                continue
        parameters[(e1, e2, e3)] = mixing_params_from_singles(e1, e2, mixing_value)
    return parameters


LAMMPS_POTENTIAL_NAME_MAPPING = {
    'lennard-jones': 'lj/cut',
    'beck': 'beck',
    'zbl': 'zbl',
    'buckingham': 'buck',
    'tersoff-2': 'tersoff',
    'tersoff': 'tersoff',
    'stillinger-weber': 'sw',
    'gao-weber': 'gw',
    'vashishta': 'vashishta',
    'vashishta-mixing': 'vashishta',
    'comb': 'comb',
    'comb-3': 'comb3',
    'python-function': 'table'
}


def write_potential_files(potential, elements, unique_id=1):
    """Generate lammps files required by specified potential

    Parameters
    ----------
    potential: dftfit.potential.Potential
        schema representation of potential
    elements: list
        list specifying the index of each element
    unique_id: str
        an id that can be used for files to guarentee uniqueness
    """
    spec = potential.schema['spec']
    lammps_files = {}
    for i, pair_potential in enumerate(spec.get('pair', [])):
        potential_lammps_name = LAMMPS_POTENTIAL_NAME_MAPPING.get(pair_potential['type'])
        if pair_potential['type'] == 'tersoff-2':
            element_parameters = {}
            mixing_parameters = {}
            for parameter in pair_potential['parameters']:
                if len(parameter['elements']) == 1:
                    element_parameters[parameter['elements'][0]] = parameter['coefficients']
                elif len(parameter['elements']) == 2:
                    mixing_parameters[tuple(sorted(parameter['elements']))] = parameter['coefficients'][0]
            parameters = tersoff_2_to_tersoff(element_parameters, mixing_parameters)
        elif pair_potential['type'] == 'vashishta-mixing':
            element_parameters = {}
            override_parameters = {}
            for parameter in pair_potential['parameters']:
                if len(parameter['elements']) == 1:
                    element_parameters[parameter['elements'][0]] = parameter['coefficients']
                elif len(parameter['elements']) == 3:
                    override_parameters[tuple(parameter['elements'])] = parameter['coefficients']
            parameters = vashishta_mixed_to_vashishta(element_parameters, override_parameters)
        elif pair_potential['type'] in {'tersoff-2', 'tersoff', 'stillinger-weber', 'gao-weber', 'vashishta', 'comb', 'comb-3', 'python-function'}:
            parameters = {}
            for parameter in pair_potential['parameters']:
                parameters[tuple(parameter['elements'])] = [float(_) for _ in parameter['coefficients']]

        filename = '/tmp/lammps.%d.%s.%s' % (i, unique_id, potential_lammps_name)
        if pair_potential['type'] in {'tersoff-2', 'tersoff'}:
            lammps_files[filename] = write_tersoff_potential(parameters)
        elif pair_potential['type'] == 'stillinger-weber':
            lammps_files[filename] = write_stillinger_weber_potential(parameters)
        elif pair_potential['type'] == 'gao-weber':
            lammps_files[filename] = write_gao_weber_potential(parameters)
        elif pair_potential['type'] in {'vashishta', 'vashishta-mixing'}:
            lammps_files[filename] = write_vashishta_potential(parameters)
        elif pair_potential['type'] == 'comb':
            lammps_files[filename] = write_comb_potential(parameters)
        elif pair_potential['type'] == 'comb-3':
            lammps_files[filename] = write_comb_3_potential(parameters)
        elif pair_potential['type'] == 'python-function':
            cutoff = [float(_) for _ in pair_potential.get('cutoff', [1.0, 10.0])]
            samples = int(pair_potential.get('samples', 1000))

            def get_function(func_str):
                d = {}
                exec(func_str, d)
                return d['potential']

            potential_func = get_function(pair_potential['function'])
            for (e1, e2), parameters in parameters.items():
                float_parameters = [float(_) for _ in parameters]
                f_r = functools.partial(potential_func, *float_parameters)
                filename = '/tmp/lammps.%s.%s.%d.%s.%s' % (e1, e2, i, unique_id, potential_lammps_name)
                lammps_files[filename] = write_table_pair_potential(f_r, samples=samples, bounds=cutoff)
    return lammps_files


def write_potential(potential, elements, unique_id=1):
    """Generate lammps commands required by specified potential

    Parameters
    ----------
    potential: dftfit.potential.Potential
        schema representation of potential
    elements: list
        list specifying the index of each element
    unique_id: str
        an id that can be used for files to guarentee uniqueness

    Supported Potentials:

    - two-body
      - lennard-jones
      - buckingham
    - three-body
      - tersoff-2, tersoff
      - stillinger-weber
      - gao-weber
    - n-body
      - coloumb charge (long + short range)
    """
    spec = potential.schema['spec']
    element_map = {e.symbol: i for i, e in enumerate(elements, start=1)}

    # collect potentials in spec
    potentials = []
    lammps_commands = []
    if ('charge' in spec) and ('kspace' in spec):
        lammps_commands.append('kspace_style %s %f' % (spec['kspace']['type'], spec['kspace']['tollerance']))
        for element, charge in spec['charge'].items():
            lammps_commands.append('set type %d charge %f' % (element_map[element], float(charge)))
        potentials.append(({
            'pair_style': 'coul/long %f' % 10.0,
            'pair_coeff': [('* *', 'coul/long', '')]
        }))

    for i, pair_potential in enumerate(spec.get('pair', [])):
        potential_lammps_name = LAMMPS_POTENTIAL_NAME_MAPPING.get(pair_potential['type'])
        if pair_potential['type'] in {'lennard-jones', 'beck', 'buckingham', 'zbl'}:
            pair_coeffs = []
            for parameter in pair_potential['parameters']:
                e1, e2 = parameter['elements']
                ij = ' '.join([str(_) for _ in sorted([element_map[e1], element_map[e2]])])
                coefficients_str = ' '.join([str(float(coeff)) for coeff in parameter['coefficients']])
                pair_coeffs.append((ij, potential_lammps_name, coefficients_str))

            if pair_potential['type'] == 'zbl':
                cutoff = pair_potential.get('cutoff', [3.0, 4.0])
                pair_style = '%s %f %f' % (potential_lammps_name, cutoff[0], cutoff[1])
            else:
                pair_style = '%s %f' % (potential_lammps_name, pair_potential.get('cutoff', [10.0])[-1])
            potentials.append({
                'pair_style': pair_style,
                'pair_coeff': pair_coeffs
            })
        elif pair_potential['type'] == 'python-function':
            pair_coeffs = []
            for parameter in pair_potential['parameters']:
                e1, e2 = parameter['elements']
                ij = ' '.join([str(_) for _ in sorted([element_map[e1], element_map[e2]])])
                filename = '/tmp/lammps.%s.%s.%d.%s.%s' % (e1, e2, i, unique_id, potential_lammps_name)
                pair_coeffs.append((ij, potential_lammps_name, '%s PAIR' % filename))

            samples = pair_potential.get('samples', 1000)
            potentials.append({
                'pair_style': 'table linear %d' % samples,
                'pair_coeff': pair_coeffs
            })
        elif pair_potential['type'] in {'tersoff-2', 'tersoff', 'stillinger-weber', 'gao-weber', 'vashishta', 'vashishta-mixing', 'comb', 'comb-3'}:
            filename = '/tmp/lammps.%d.%s.%s' % (i, unique_id, potential_lammps_name)
            if pair_potential['type'] == 'comb-3':
                pair_style = '%s polar_off' % (potential_lammps_name)
            else:
                pair_style = potential_lammps_name
            potentials.append({
                'pair_style': pair_style,
                'pair_coeff': [('* *', potential_lammps_name, '%s %s' % (
                    filename, ' '.join(str(e) for e in elements)))],
            })
        else:
            raise ValueError('pair potential %s not implemented yet!' % (pair_potential['type']))

    if len(potentials) == 1:  # no need for hybrid/overlay
        potential = potentials[0]
        lammps_commands.append('pair_style %s' % potential['pair_style'])
        for pair_coeff in potential['pair_coeff']:
            lammps_commands.append('pair_coeff ' + pair_coeff[0] + ' ' + pair_coeff[2])
    elif len(potentials) > 1:  # use hybrid/overlay to join all potentials
        lammps_commands.append('pair_style hybrid/overlay ' + ' '.join(potential['pair_style'] for potential in potentials))
        for potential in potentials:
            for pair_coeff in potential.get('pair_coeff', []):
                lammps_commands.append('pair_coeff ' + ' '.join(pair_coeff))
    return lammps_commands
