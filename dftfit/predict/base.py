import asyncio
import os
import json

from lammps.inputs import LammpsScript
from lammps.sets import MODULE_DIR
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core import Lattice

from ..io.lammps import LammpsLocalCalculator


def load_lammps_set(config_filename):
    with open(os.path.join(MODULE_DIR, 'sets', config_filename + ".json")) as f:
        return json.load(f, object_pairs_hook=LammpsScript)


class Predict:
    def __init__(self, calculator='lammps', loop=None, **kwargs):
        calculator_mapper = {
            'lammps': LammpsLocalCalculator
        }
        self.calculator = calculator_mapper[calculator](**kwargs)
        self.loop = loop or asyncio.get_event_loop()
        self.loop.run_until_complete(self.calculator.create())

    def lattice_constant(self, structure, potential):
        sga = SpacegroupAnalyzer(structure)
        conventional_structure = sga.get_conventional_standard_structure()

        async def calculate():
            future = await self.calculator.submit(
                conventional_structure, potential,
                properties={'lattice'},
                lammps_set=load_lammps_set('relax'))
            await future
            return future.result()

        result = self.loop.run_until_complete(calculate())
        lattice = Lattice(result['results']['lattice'])
        return conventional_structure.lattice, lattice

    def elastic_constant(self, structure, potential):
        pass
