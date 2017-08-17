from pathlib import Path
from collections import OrderedDict
import subprocess

from lammps.output import LammpsRun, LammpsData
from lammps.inputs import LammpsInput, LammpsScript

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
    ('thermo_style', 'custom step etotal pxx pyy pzz pxy pxz pyz'),
    ('run', 0)
])


class LammpsWriter(MDWriter):
    def __init__(self, structure, potential):
        self.structure = structure
        if not isinstance(potential, Potential):
            potential = Potential(potential)

        self.potential = potential.schema # TODO: Hack potential should do more work
        self.data = LammpsData.from_structure(self.structure)
        self.symbol_indicies = {element_type_to_symbol(s): i for s, i in self.data.symbol_indicies.items()}
        lammps_script = LammpsScript(lammps_dftfit_set)
        lammps_script.update([self.charge, self.kspace_style, self.pair_style, self.pair_coeff])
        self.lammps_input = LammpsInput(lammps_script, self.data)

    def write_input(self, directory):
        self.lammps_input.write_input(directory)

    @property
    def charge(self):
        spec = self.potential['spec']
        set_commands = []
        for element, charge in spec.get('charge', {}).items():
            set_commands.append('type %d charge %f' % (self.symbol_indicies[element], float(charge)))
        return ('set', set_commands)

    @property
    def kspace_style(self):
        spec = self.potential['spec']
        if 'kspace' in spec:
            style = spec['kspace']['type']
            tollerance = spec['kspace']['tollerance']
            return ('kspace_style', '%s %f' % (style, float(tollerance)))
        return ('kspace_style', [])

    @property
    def pair_style(self):
        pair_map = {
            'buckingham': 'buck'
        }

        spec = self.potential['spec']
        if 'pair' in spec:
            style = pair_map[spec['pair']['type']]
            cutoff = spec['pair']['cutoff']
            if 'kspace'in spec and spec['kspace']['type'] in {'ewald', 'pppm'}:
                style += '/coul/long'
            return ('pair_style', '%s %f' % (style, float(cutoff)))
        return ('pair_style', [])

    @property
    def pair_coeff(self):
        spec = self.potential['spec']
        if 'pair' in spec:
            symbols_to_indicies = lambda symbols: [self.symbol_indicies[s] for s in symbols]
            pair_coeffs = []
            for coeff in spec['pair']['parameters']:
                pair_coeffs.append(' '.join(list(map(str, symbols_to_indicies(coeff['elements']) + coeff['coefficients']))))
            return ('pair_coeff', pair_coeffs)
        return ('pair_coeff', [])


class LammpsRunner(MDRunner):
    def run(self, writer, command=None, directory=None):
        directory = directory or '.'
        command = command or ['lammps']
        writer.write_input(directory)
        return_code, stdout, stderr = self._run(command, directory)
        if return_code != 0:
            raise ValueError('Lammps calculation exited with non zero return code', stdout, stderr)
        return LammpsReader(directory)
