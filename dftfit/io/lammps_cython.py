import math
import itertools

import lammps
import numpy as np

from .base import DFTFITCalculator, MDReader


class LammpsCythonDFTFITCalculator(DFTFITCalculator):
    """This is not a general purpose lammps calculator. Only for dftfit
    evaluations. For now there are not plans to generalize it.
    """
    def __init__(self, structures, num_workers=1):
        if num_workers != 1:
            raise NotImplemented('For now limited to one worker')
        self.structures = structures
        self.elements = []
        self.lammps_systems = []

    def _initialize_lammps(self, structure):
        lmp = lammps.Lammps(units='metal', style='full', args=[
            '-log', 'none', '-screen', 'none'
        ])
        lmp.command('atom_modify map yes')
        atom_types = np.array([self.elements.index(atom.specie)+1 for atom in structure], dtype=np.intc)

        # lammps does not handle non-orthogonal cells well
        if not structure.lattice.is_orthogonal:
            lmp.command('box tilt large')
        rotation_matrix, origin = lmp.box.from_lattice_const(
            len(self.elements),
            np.array(structure.lattice.abc),
            np.array(structure.lattice.angles) * (math.pi/180))
        for element, atom_type in zip(self.elements, lmp.system.atom_types):
            atom_type.mass = element.atomic_mass

        cart_coords = lammps.core.transform_cartesian_vector_to_lammps_vector(structure.cart_coords, rotation_matrix, origin)
        lmp.system.create_atoms(atom_types, cart_coords+1e-8)
        lmp.thermo.add('my_ke', 'ke', 'all')
        return lmp

    async def create(self):
        # ensure element indexes are the same between all lammps calculations
        self.elements = set()
        for structure in self.structures:
            self.elements = self.elements | set(structure.species)
        self.elements = list(self.elements)

        for structure in self.structures:
            self.lammps_systems.append(self._initialize_lammps(structure))

    def _apply_potential_files(self, potential):
        """Since potential do not change between all structures we only need
        to write files once per submit
        """
        spec = potential.schema['spec']
        if ('pair' in spec) and (spec['pair']['type'] == 'tersoff-2'):
            self._apply_file_tersoff_2(potential)

    def _apply_file_tersoff_2(self, potential, filename='/tmp/lammps.tersoff-2'):
        spec = potential.schema['spec']
        element_values = {p['elements'][0]: p['coefficients'] for p in spec['pair']['parameters'] if len(p['elements']) == 1}
        mixing_values = {tuple(sorted(p['elements'])): p['coefficients'] for p in spec['pair']['parameters'] if len(p['elements']) == 2}

        def mixing_params_from_singles(e1, e2):
            p1 = [float(_) for _ in element_values[e1]]
            p2 = [float(_) for _ in element_values[e2]]
            mixing = float(mixing_values.get(tuple(sorted([e1, e2])), [1.0])[0])
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

        with open(filename, 'w') as f:
            for e1, e2, e3 in itertools.product(element_values, repeat=3):
                f.write(' '.join([e1, e2, e3] + ['{:16.8g}'.format(_) for _ in  mixing_params_from_singles(e1, e2)]) + '\n')

    def _apply_potential(self, lmp, potential):
        """Apply specific potential

        Wish that this was more generic. But I have found that simpler
        implementation is better for now.
        """

        spec = potential.schema['spec']

        if ('charge' in spec) and ('kspace' in spec) and ('pair' in spec) and ('nbody' in spec) and \
           (spec['pair']['type'] == 'buckingham') and (spec['nbody']['type'] == 'harmonic'):
            raise ValueError('Sadly lammps cannot implement 3-body angle with differing species')
        elif ('charge' in spec) and ('kspace' in spec) and ('pair' in spec) and \
             (spec['pair']['type'] == 'buckingham'):
            self._apply_buckingham_charge(lmp, potential)
        elif ('pair' in spec) and (spec['pair']['type'] == 'tersoff-2'):
            self._apply_tersoff_2(lmp, potential)

    def _apply_buckingham_charge(self, lmp, potential):
        element_map = {e.symbol: i for i, e in enumerate(self.elements, start=1)}
        spec = potential.schema['spec']
        lmp.command('kspace_style %s %f' % (
            spec['kspace']['type'], spec['kspace']['tollerance']))
        lmp.command('pair_style buck/coul/long %f' % spec['pair']['cutoff'])
        for parameter in spec['pair']['parameters']:
            ij = sorted([element_map[parameter['elements'][0]],
                         element_map[parameter['elements'][1]]])
            lmp.command('pair_coeff %d %d %s' % (
                ij[0], ij[1],
                ' '.join([str(float(coeff)) for coeff in parameter['coefficients']])))
        for element, charge in spec['charge'].items():
            lmp.command('set type %d charge %f' % (element_map[element], float(charge)))

    def _apply_tersoff_2(self, lmp, potential):
        lmp.command('pair_style tersoff')
        lmp.command('pair_coeff * * /tmp/lammps.tersoff-2 %s' % ' '.join(str(e) for e in self.elements))

    async def submit(self, potential, properties=None):
        properties = properties or {'stress', 'energy', 'forces'}
        results = []
        self._apply_potential_files(potential)
        for lmp, structure in zip(self.lammps_systems, self.structures):
            self._apply_potential(lmp, potential)
            lmp.run(0)
            S = lmp.thermo.computes['thermo_press'].vector
            results.append(MDReader(
                forces=lmp.system.forces.copy(),
                energy=lmp.thermo.computes['thermo_pe'].scalar + lmp.thermo.computes['my_ke'].scalar,
                stress=np.array([
                    [S[0], S[3], S[5]],
                    [S[3], S[1], S[4]],
                    [S[5], S[4], S[2]]
                ]),
                structure=structure))
        return results

    def shutdown(self):
        pass
