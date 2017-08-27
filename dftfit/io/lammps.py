from pathlib import Path
from collections import OrderedDict
import subprocess
import tempfile
import asyncio
import os

from lammps.output import LammpsRun, LammpsData
from lammps.inputs import LammpsInput, LammpsScript
from lammps.calculator import LammpsCalculator

from .base import MDReader, MDWriter, MDRunner
from .utils import element_type_to_symbol
from ..potential import Potential



class LammpsReader(MDReader):
    def __init__(self, directory, data_filename='initial.data', log_filename='lammps.log', dump_filename='mol.lammpstrj'):
        self.directory = Path(directory)
        self.data_filename = data_filename
        self.log_filename = log_filename
        self.dump_filename = dump_filename
        self._parse()

    def _parse(self):
        dump_path = list(self.directory.glob('**/%s' % self.dump_filename))
        if len(dump_path) > 1:
            raise ValueError('multiple %s files found within directory' % self.dump_filename)
        elif len(dump_path) == 0:
            raise ValueError('could not find %s file within directory' % self.dump_filename)

        log_path = list(self.directory.glob('**/%s' % self.log_filename))
        if len(log_path) > 1:
            raise ValueError('multiple %s files found within directory' % self.log_filename)
        elif len(log_path) == 0:
            raise ValueError('could not find %s file within directory' % self.log_filename)

        data_path = list(self.directory.glob('**/%s' % self.data_filename))
        if len(data_path) > 1:
            raise ValueError('multiple %s files found within directory' % self.data_filename)
        elif len(data_path) == 0:
            raise ValueError('could not find %s file within directory' % self.data_filename)

        data = LammpsData.from_file(str(data_path[0]))
        output = LammpsRun(str(data_path[0]), lammps_log=str(log_path[0]), lammps_dump=str(dump_path[0]))
        # TODO: check units
        self._forces = output.get_forces(-1)
        self._stress = output.get_stress(-1)
        self._energy = output.get_energy(-1)
        self._structure = output.get_structure(-1)

    @property
    def forces(self):
        return self._forces

    @property
    def stress(self):
        return self._stress

    @property
    def energy(self):
        return self._energy

    @property
    def structure(self):
        return self._structure


lammps_dftfit_set = OrderedDict([
    ('echo', 'both'),
    ('log', 'lammps.log'),
    ('units', 'metal'),
    ('dimension', 3),
    ('boundary', 'p p p'),
    ('atom_style', 'full'),
    ('read_data', 'initial.data'),
    ('kspace_style', []),
    ('pair_style', []),
    ('pair_coeff', []),
    ('set', []),
    ('dump', '1 all custom 1 mol.lammpstrj id type x y z fx fy fz'),
    ('dump_modify', '1 sort id'),
    ('thermo_modify', 'flush yes'),
    ('thermo_style', 'custom step etotal pxx pyy pzz pxy pxz pyz'),
    ('run', 0),
])


class LammpsWriter(MDWriter):
    def __init__(self, structure, potential):
        if not isinstance(potential, Potential):
            potential = Potential(potential)

        self.lammps_input = LammpsInput(
            LammpsScript(lammps_dftfit_set),
            LammpsData.from_structure(structure)
        )
        modify_input_for_potential(self.lammps_input, potential)

    def write_input(self, directory):
        self.lammps_input.write_input(directory)


def modify_input_for_potential(lammps_input, potential):
    symbol_indicies = {element_type_to_symbol(s): i for s, i in lammps_input.lammps_data.symbol_indicies.items()}

    def charge(potential):
        spec = potential.schema['spec']
        set_commands = []
        for element, charge in spec.get('charge', {}).items():
            set_commands.append('type %d charge %f' % (symbol_indicies[element], float(charge)))
        return ('set', set_commands)

    def kspace_style(potential):
        spec = potential.schema['spec']
        if 'kspace' in spec:
            style = spec['kspace']['type']
            tollerance = spec['kspace']['tollerance']
            return ('kspace_style', '%s %f' % (style, float(tollerance)))
        return ('kspace_style', [])

    def pair_style(potential):
        pair_map = {
            'buckingham': 'buck'
        }

        spec = potential.schema['spec']
        if 'pair' in spec:
            style = pair_map[spec['pair']['type']]
            cutoff = spec['pair']['cutoff']
            if 'kspace'in spec and spec['kspace']['type'] in {'ewald', 'pppm'}:
                style += '/coul/long'
            return ('pair_style', '%s %f' % (style, float(cutoff)))
        return ('pair_style', [])

    def pair_coeff(potential):
        spec = potential.schema['spec']
        if 'pair' in spec:
            symbols_to_indicies = lambda symbols: [symbol_indicies[s] for s in symbols]
            pair_coeffs = []
            for coeff in spec['pair']['parameters']:
                pair_coeffs.append(' '.join(list(map(str, symbols_to_indicies(coeff['elements']) + coeff['coefficients']))))
            return ('pair_coeff', pair_coeffs)
        return ('pair_coeff', [])

    lammps_input.lammps_script.update([
        charge(potential),
        kspace_style(potential),
        pair_style(potential),
        pair_coeff(potential)
    ])


# should turn into async context manager
class LammpsRunner(MDRunner):
    def __init__(self, calculations, cmd=None, max_workers=1):
        self.calculations = calculations
        self.cmd = cmd or ['lammps']
        self.max_workers = max_workers

    async def initialize(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.lammps_calculator = LammpsCalculator(max_workers=self.max_workers, cwd=str(self.tempdir.name), cmd=self.cmd)
        await self.lammps_calculator._create()

        for i, calculation in enumerate(self.calculations):
            data_file = LammpsData.from_structure(calculation.structure)
            data_file.write_file(Path(self.tempdir.name) / ('initial.%d.data' % i))

    @classmethod
    def run_single(cls, lammps_input, command='lammps', run_directory='.'):
        lammps_input.write_input(run_directory)
        cls._run(command, run_directory)
        return LammpsReader(run_directory)

    async def calculate(self, potential):
        writer = LammpsWriter(self.calculations.calculations[0].structure, potential)
        script = writer.lammps_input.lammps_script

        # Run Calculations
        lammps_futures = []
        for i, calculation in enumerate(self.calculations):
            script['read_data'] = 'initial.%d.data' % i
            script['log'] = 'lammps.%d.log' % i
            dump = str(script.get('dump')).split()
            dump[4] = 'mol.%d.lammpstrj' % i
            script['dump'] = ' '.join(dump)
            lammps_futures.append(await self.lammps_calculator.submit(script))
            await asyncio.sleep(1e-6) # TODO: why needed?
            # import pdb; pdb.set_trace()
        results = await asyncio.gather(*lammps_futures)
        # for result in results:
        #     print(result)

        # import pdb; pdb.set_trace()
        # Parse Calculations
        calculations = []
        for i, calculation in enumerate(self.calculations):
            calculations.append(LammpsReader(
                self.tempdir.name,
                data_filename='initial.%d.data' % i,
                log_filename='lammps.%d.log' % i,
                dump_filename='mol.%d.lammpstrj' % i))
        return calculations

    async def finalize(self):
        self.tempdir.cleanup()
