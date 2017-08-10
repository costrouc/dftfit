from pathlib import Path
from collections import OrderedDict

from lammps.output import LammpsRun, LammpsData
from lammps.inputs import LammpsInput, LammpsScript

from .base import MDReader, MDWriter


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
        self._energy = output.lammps_log.thermo_data['etotal'][-1]
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
    ('pair_style', []),
    ('kspace_style', []),
    ('read_data', 'initial.data'),
    ('dump', '1 all custom 1 mol.lammpstrj id type x y z fx fy fz'),
    ('dump_modify', '1 sort id'),
    ('thermo_style', 'custom step etotal pxx pyy pzz pxy pxz pyz'),
    ('run', 0)
])


class LammpsWriter(MDWriter):
    def __init__(self, structure, potentials, user_lammps_settings=None):
        self.data = LammpsData.from_structure(structure, potentials, include_charge=True)
        lammps_script = LammpsScript(lammps_dftfit_set)
        lammps_script.update(user_lammps_settings or [])
        self.lammps_input = LammpsInput(lammps_script, self.data)

    def write_input(self, directory):
        self.lammps_input.write_input(directory)
