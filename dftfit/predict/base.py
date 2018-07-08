import asyncio
import os
import json

import numpy as np

from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core import Lattice, Structure
from pymatgen.analysis.elasticity import DeformedStructureSet, ElasticTensor, Stress, Strain


from ..io.lammps import LammpsLocalMDCalculator


def load_lammps_set(config_filename):
    from pmg_lammps.sets import MODULE_DIR
    from pmg_lammps.inputs import LammpsScript

    with open(os.path.join(MODULE_DIR, 'sets', config_filename + ".json")) as f:
        return json.load(f, object_pairs_hook=LammpsScript)


class Predict:
    def __init__(self, calculator='lammps', loop=None, **kwargs):
        calculator_mapper = {
            'lammps': LammpsLocalMDCalculator
        }
        self.calculator = calculator_mapper[calculator](**kwargs)
        self.loop = loop or asyncio.get_event_loop()
        self.loop.run_until_complete(self.calculator.create())

    def conventional_structure(self, structure):
        sga = SpacegroupAnalyzer(structure)
        return sga.get_conventional_standard_structure()

    def static(self, structure, potential):
        async def calculate():
            future = await self.calculator.submit(
                structure, potential,
                properties={'forces', 'stress', 'energy'},
                lammps_set=load_lammps_set('static'))
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
                    lammps_set=load_lammps_set('static')))
            return await asyncio.gather(*futures)
        results = self.loop.run_until_complete(calculate())
        return np.array([r['results']['energy'] for r in results])

    def lattice_constant(self, structure, potential, supercell=(1, 1, 1), etol=1e-6, ftol=1e-6):
        conventional_structure = self.conventional_structure(structure)

        async def calculate():
            relax_lammps_script = load_lammps_set('relax')
            relax_lammps_script['minimize'] = '%f %f 2000 10000' % (etol, ftol)
            future = await self.calculator.submit(
                conventional_structure * supercell, potential,
                properties={'lattice'},
                lammps_set=relax_lammps_script)
            await future
            return future.result()

        result = self.loop.run_until_complete(calculate())
        lattice = Lattice(result['results']['lattice'])
        return conventional_structure.lattice, Lattice(lattice.matrix / np.array(supercell))

    def elastic_constant(self, structure, potential, supercell=(1, 1, 1),
                         nd=0.01, ns=0.05, num_norm=4, num_shear=4,
                         etol=1e-6, ftol=1e-6):
        conventional_structure = self.conventional_structure(structure)
        deformation_set = DeformedStructureSet(conventional_structure * supercell,
                                               nd=nd, ns=ns,
                                               num_norm=num_norm, num_shear=num_shear)
        strains = []
        stresses = []

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
                    lammps_set=relax_lammps_script))
            for result in await asyncio.gather(*futures):
                stress = Stress(np.array(result['results']['stress']) * 1e-4) # Convert to GPa
                stresses.append(stress)

        self.loop.run_until_complete(calculate())
        return ElasticTensor.from_pseudoinverse(strains, stresses)
