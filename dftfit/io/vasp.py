from pathlib import Path

import numpy as np
from pymatgen.io.vasp import Vasprun

from .base import DFTReader


class VaspReader(DFTReader):
    def __init__(self, directory, vasprun_filename='vasprun.xml'):
        self.directory = Path(directory)
        self.vasprun_filename = vasprun_filename
        if not self.directory.is_dir():
            raise ValueError('path %s must exist and be directory' % self.directory)
        self._parse()

    def _parse(self):
        vasprun_path = list(self.directory.glob('**/%s' % self.vasprun_filename))
        if len(vasprun_path) > 1:
            raise ValueError('multiple vasprun.xml files found within directory')
        elif len(vasprun_path) == 0:
            raise ValueError('could not find vasprun.xml file within directory')

        vasprun = Vasprun(str(vasprun_path[0]))
        self._forces = np.array(vasprun.ionic_steps[-1]['forces'])
        self._stress = np.array(vasprun.ionic_steps[-1]['stress']) * 1e3 # kbar -> bar
        self._energy = float(vasprun.final_energy)
        self._structure = vasprun.final_structure

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
