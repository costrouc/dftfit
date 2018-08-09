import asyncio
import os
import json

import numpy as np

from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core import Lattice, Structure
from pymatgen.analysis.elasticity import DeformedStructureSet, ElasticTensor, Stress, Strain


from ..io.lammps import LammpsLocalMDCalculator
from ..io.lammps_cython import LammpsCythonMDCalculator


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
        self.loop.run_until_complete(self.calculator.create())

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
        result = self.loop.run_until_complete(calculate())
        return {
            'energy': result['results']['energy'],
            'stress': np.array(result['results']['stress']) * 1e-4,  # convert to GPa
            'forces': np.array(result['results']['forces'])
        }

    def pair(self, specie_a, specie_b, potential, separations):
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
                    [specie_a, specie_b],
                    [coord_a, coord_b], coords_are_cartesian=True)
                futures.append(await self.calculator.submit(
                    structure, potential,
                    properties={'energy'},
                    **kwargs))
            return await asyncio.gather(*futures)
        results = self.loop.run_until_complete(calculate())
        return np.array([r['results']['energy'] for r in results])

    def lattice_constant(self, structure, potential, supercell=(1, 1, 1), etol=1e-6, ftol=1e-6):
        conventional_structure = self.conventional_structure(structure)

        if self.calculator_type == 'lammps':
            relax_lammps_script = load_lammps_set('relax')
            relax_lammps_script['minimize'] = '%f %f 2000 10000' % (etol, ftol)
            kwargs = {'lammps_set': relax_lammps_script}
        elif self.calculator_type == 'lammps_cython':
            kwargs = {'lammps_additional_commands': [
                'fix 1 all box/relax iso 0.0 vmax 0.001',
                'min_style cg',
                'minimize %f %f 2000 10000' % (etol, ftol)
            ]}

        async def calculate():
            future = await self.calculator.submit(
                conventional_structure * supercell, potential,
                properties={'lattice'},
                **kwargs)
            await future
            return future.result()

        result = self.loop.run_until_complete(calculate())
        lattice = Lattice(result['results']['lattice'])
        return conventional_structure.lattice, Lattice(lattice.matrix / np.array(supercell))

    def elastic_constant(self, structure, potential, supercell=(1, 1, 1),
                         nd=0.01, ns=0.05, num_norm=4, num_shear=4,
                         etol=1e-6, ftol=1e-6):
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
            relax_lammps_script['minimize'] = '%f %f 2000 10000' % (etol, ftol)
            kwargs = {'lammps_set': relax_lammps_script}
        elif self.calculator_type == 'lammps_cython':
            kwargs = {'lammps_additional_commands': [
                'min_style cg',
                'minimize %f %f 2000 10000' % (etol, ftol)
            ]}

        async def calculate():
            relax_lammps_script = load_lammps_set('relax')
            relax_lammps_script['fix'] = []
            relax_lammps_script['minimize'] = '%f %f 2000 10000' % (etol, ftol)
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

        self.loop.run_until_complete(calculate())
        return ElasticTensor.from_independent_strains(strains, stresses, Stress(np.zeros((3, 3))))
