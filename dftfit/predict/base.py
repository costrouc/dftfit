import asyncio
import os
import json
import math
import copy
import logging
import time

import numpy as np
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core import Lattice, Structure, Element
from pymatgen.analysis.elasticity import DeformedStructureSet, ElasticTensor, Stress, Strain
from pymatgen.util.coord import pbc_diff

from ..io.lammps import LammpsLocalMDCalculator
from ..io.lammps_cython import LammpsCythonMDCalculator
from .utils import apply_structure_operations

logger = logging.getLogger(__name__)


def load_lammps_set(config_filename):
    from pmg_lammps.sets import MODULE_DIR
    from pmg_lammps.inputs import LammpsScript

    with open(os.path.join(MODULE_DIR, 'sets', config_filename + ".json")) as f:
        return json.load(f, object_pairs_hook=LammpsScript)


class Predict:
    def __init__(self, calculator='lammps_cython', loop=None, **kwargs):
        calculator_mapper = {
            'lammps': LammpsLocalMDCalculator,
            'lammps_cython': LammpsCythonMDCalculator
        }
        self.calculator_type = calculator
        self.calculator = calculator_mapper[calculator](**kwargs)
        self.loop = loop or asyncio.get_event_loop()
        self._run_async_func(self.calculator.create())

    def _run_async_func(self, async_function):
        """Added to handle other application that manager event loop

        Jupyter uses the event loop with tornado. Compatibility see
        https://github.com/jupyter/notebook/issues/3397

        See https://github.com/erdewit/nest_asyncio
        """
        return self.loop.run_until_complete(async_function)

    def conventional_structure(self, structure):
        sga = SpacegroupAnalyzer(structure)
        return sga.get_conventional_standard_structure()

    def material_properties(self, structure, potential, properties=None):
        properties = properties or {'lattice_constants'}
        raise NotImplementedError()

    def static(self, structure, potential):
        if self.calculator_type == 'lammps':
            kwargs = {'lammps_set': load_lammps_set('static')}
        elif self.calculator_type == 'lammps_cython':
            kwargs = {'lammps_additional_commands': ['run 0']}

        async def calculate():
            future = await self.calculator.submit(
                structure, potential,
                properties={'forces', 'stress', 'energy'},
                **kwargs)
            await future
            return future.result()
        result = self._run_async_func(calculate())
        return {
            'energy': result['results']['energy'],
            'stress': np.array(result['results']['stress']) * 1e-4,  # convert to GPa
            'forces': np.array(result['results']['forces'])
        }

    def pair(self, element_a, element_b, potential, separations):
        max_r = np.max(separations)
        lattice = Lattice.from_parameters(10*max_r, 10*max_r, 10*max_r, 90, 90, 90)

        if self.calculator_type == 'lammps':
            kwargs = {'lammps_set': load_lammps_set('static')}
        elif self.calculator_type == 'lammps_cython':
            kwargs = {'lammps_additional_commands': ['run 0']}

        async def calculate():
            futures = []
            for sep in separations:
                coord_a = (lattice.a*0.5-(sep/2), lattice.b*0.5, lattice.c*0.5)
                coord_b = (lattice.a*0.5+(sep/2), lattice.b*0.5, lattice.c*0.5)
                structure = Structure(
                    lattice,
                    [element_a, element_b],
                    [coord_a, coord_b], coords_are_cartesian=True)
                futures.append(await self.calculator.submit(
                    structure, potential,
                    properties={'energy'},
                    **kwargs))
            return await asyncio.gather(*futures)
        results = self._run_async_func(calculate())
        return np.array([r['results']['energy'] for r in results])

    def three_body(self, element_a, element_b, potential, separation, angles):
        max_r = separation
        lattice = Lattice.from_parameters(10*max_r, 10*max_r, 10*max_r, 90, 90, 90)

        if self.calculator_type == 'lammps':
            kwargs = {'lammps_set': load_lammps_set('static')}
        elif self.calculator_type == 'lammps_cython':
            kwargs = {'lammps_additional_commands': ['run 0']}

        async def calculate():
            futures = []
            for angle in angles:
                coord_a = (lattice.a*0.5 + separation, lattice.b*0.5, lattice.c*0.5)
                coord_b = (lattice.a*0.5, lattice.b*0.5, lattice.c*0.5) # b in center
                coord_c = (lattice.a*0.5 + (math.cos(angle) * separation), lattice.b*0.5 + (math.sin(angle) * separation), lattice.c*0.5)
                structure = Structure(
                    lattice,
                    [element_b, element_a, element_b],
                    [coord_a, coord_b, coord_c], coords_are_cartesian=True)
                futures.append(await self.calculator.submit(
                    structure, potential,
                    properties={'energy'},
                    **kwargs))
            return await asyncio.gather(*futures)
        results = self._run_async_func(calculate())
        return np.array([r['results']['energy'] for r in results])

    def lattice_constant(self, structure, potential, supercell=(1, 1, 1), etol=1e-6, ftol=1e-6, nsearch=2000, neval=10000):
        conventional_structure = self.conventional_structure(structure)

        if self.calculator_type == 'lammps':
            relax_lammps_script = load_lammps_set('relax')
            relax_lammps_script['minimize'] = '%f %f %d %d' % (etol, ftol, nsearch, neval)
            kwargs = {'lammps_set': relax_lammps_script}
        elif self.calculator_type == 'lammps_cython':
            kwargs = {'lammps_additional_commands': [
                'fix 1 all box/relax iso 0.0 vmax 0.001',
                'min_style cg',
                'minimize %f %f %d %d' % (etol, ftol, nsearch, neval)
            ]}

        async def calculate():
            future = await self.calculator.submit(
                conventional_structure * supercell, potential,
                properties={'lattice'},
                **kwargs)
            await future
            return future.result()

        result = self._run_async_func(calculate())
        lattice = Lattice(result['results']['lattice'])
        return conventional_structure.lattice, Lattice(lattice.matrix / np.array(supercell))

    def elastic_constant(self, structure, potential, supercell=(1, 1, 1),
                         nd=0.01, ns=0.05, num_norm=4, num_shear=4,
                         etol=1e-6, ftol=1e-6, nsearch=2000, neval=10000):
        norm_strains = np.linspace(-nd, nd, num_norm).tolist()
        shear_strains = np.linspace(-ns, ns, num_shear).tolist()
        conventional_structure = self.conventional_structure(structure)
        deformation_set = DeformedStructureSet(conventional_structure * supercell,
                                               norm_strains=norm_strains,
                                               shear_strains=shear_strains)
        strains = []
        stresses = []

        if self.calculator_type == 'lammps':
            relax_lammps_script = load_lammps_set('relax')
            relax_lammps_script['fix'] = []
            relax_lammps_script['minimize'] = '%f %f %d %d' % (etol, ftol, nsearch, neval)
            kwargs = {'lammps_set': relax_lammps_script}
        elif self.calculator_type == 'lammps_cython':
            kwargs = {'lammps_additional_commands': [
                'min_style cg',
                'minimize %f %f %d %d' % (etol, ftol, nsearch, neval)
            ]}

        async def calculate():
            futures = []
            for deformation, deformed_structure in zip(deformation_set.deformations, deformation_set):
                strains.append(Strain.from_deformation(deformation))
                futures.append(await self.calculator.submit(
                    deformed_structure, potential,
                    properties={'stress'},
                    **kwargs))
            for result in await asyncio.gather(*futures):
                stress = Stress(np.array(result['results']['stress']) * 1e-4) # Convert to GPa
                stresses.append(stress)

        self._run_async_func(calculate())
        return ElasticTensor.from_independent_strains(strains, stresses, Stress(np.zeros((3, 3))))

    def point_defects(self, structure, potential, point_defect_schemas, supercell=(1, 1, 1), etol=1e-6, ftol=1e-6, nsearch=2000, neval=10000):
        """ Calculate the energy of each defect.

        structure is assumed to be the relaxed structure. This can take a long time (1-2 minutes per relaxation)
        """
        if self.calculator_type == 'lammps':
            relax_lammps_script = load_lammps_set('relax')
            relax_lammps_script['fix'] = []
            relax_lammps_script['minimize'] = '%f %f %d %d' % (etol, ftol, nsearch, neval)
            kwargs = {'lammps_set': relax_lammps_script}
        elif self.calculator_type == 'lammps_cython':
            kwargs = {'lammps_additional_commands': [
                'min_style cg',
                'minimize %f %f %d %d' % (etol, ftol, nsearch, neval)
            ]}

        energies = {}
        point_defect_schemas = copy.deepcopy(point_defect_schemas)
        for point_defect_name, operations in point_defect_schemas.items():
            base_structure = structure.copy()
            for operation in operations:
                cart_coords = base_structure.lattice.get_cartesian_coords(operation['position'])
                operation['position'] = cart_coords

            base_structure = base_structure * supercell
            apply_structure_operations(base_structure, operations)

            async def calculate():
                future = await self.calculator.submit(
                    base_structure, potential,
                    properties={'energy', 'timesteps'},
                    **kwargs)
                await future
                return future.result()

            logger.info('starting calculation (point defect): %s' % point_defect_name)
            result = self._run_async_func(calculate())
            num_eval = result['results']['timesteps']
            logger.info('finished calculation (point defect): %s in evals: %d' % (point_defect_name, num_eval))
            energies[point_defect_name] = result['results']['energy']
        return energies

    def displacement_energies(self, structure, potential, displacement_energies_schema, supercell=(1, 1, 1), tollerance=0.1, max_displacement_energy=75, resolution=1, num_steps=1000, site_radius=0.5, timestep=0.001):
        """ Calculate displacement energy for each atom.

        Uses bisection method to determine displacement energy.
        """
        def ev2Aps(Z, energy):
            # sqrt((2 * energy[eV] [J/eV]) / (amu [g/mole] [kg/g])) * [m/s] [A/ps]
            return math.sqrt((2 * energy * 1.6021766208e-19) / (Z / (6.02214085e23 * 1e3))) * 1e-2

        if self.calculator_type == 'lammps':
            logger.warning('"lammps" calculator is depriciated use "lammps_cython" cannot promise working')
            relax_lammps_script = load_lammps_set('nve')
            relax_lammps_script['thermo'] = []
            relax_lammps_script
            relax_lammps_script['timestep'] = timestep # fs
            relax_lammps_script['run'] = num_steps
            kwargs = {'lammps_set': relax_lammps_script}
        elif self.calculator_type == 'lammps_cython':
            kwargs = {'lammps_additional_commands': [
                'timestep %f' % timestep,
                'velocity all zero linear',
                'fix 1 all nve',
                'run %d' % num_steps
            ]}

        energies = {}
        displacement_energies_schema = displacement_energies_schema.copy()
        for displacement_energy_name, d in displacement_energies_schema.items():
            base_structure = structure.copy()
            v = base_structure.lattice.get_cartesian_coords(d['direction'])
            cart_coords = base_structure.lattice.get_cartesian_coords(d['position'])
            base_structure = base_structure * supercell
            site = base_structure.get_sites_in_sphere(cart_coords, tollerance)[0][0]
            original_positions = base_structure.cart_coords
            original_frac_positions = base_structure.lattice.get_fractional_coords(original_positions)
            index = base_structure.index(site)

            min_energy, max_energy = 0.0, max_displacement_energy
            guess_energy = None
            while abs(max_energy - min_energy) > resolution:
                guess_energy = (max_energy - min_energy) / 2 + min_energy
                velocity = (v / np.linalg.norm(v)) * ev2Aps(Element(d['element']).atomic_mass, guess_energy)
                velocities = np.zeros((len(base_structure), 3))
                velocities[index] = velocity
                base_structure.add_site_property('velocities', velocities)

                async def calculate():
                    future = await self.calculator.submit(
                        base_structure, potential,
                        properties={'positions', 'initial_positions'},
                        **kwargs)
                    await future
                    return future.result()

                print('starting calculation (displacement energy): %s ion %s velocity: %f [eV] %f [A/ps]' % (displacement_energy_name, d['element'], guess_energy, ev2Aps(Element(d['element']).atomic_mass, guess_energy)))
                result = self._run_async_func(calculate())
                initial_frac_positions = base_structure.lattice.get_fractional_coords(result['results']['initial_positions'])
                final_frac_positions = base_structure.lattice.get_fractional_coords(result['results']['positions'])
                displacements = np.linalg.norm(
                    base_structure.lattice.get_cartesian_coords(
                        pbc_diff(final_frac_positions, initial_frac_positions)), axis=1)
                is_original_state = np.all(displacements < site_radius)
                print('finished calculation (displacement energy): %s resulted in ground_state (%s) max displacment %f [A] median %f [A] min %f [A]' % (displacement_energy_name, is_original_state, np.max(displacements), np.median(displacements), np.min(displacements)))
                if is_original_state:
                    min_energy = guess_energy
                else:
                    max_energy = guess_energy

            energies[displacement_energy_name] = guess_energy
        return energies
