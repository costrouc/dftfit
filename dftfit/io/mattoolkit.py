import shelve
import os

import numpy as np

from .base import DFTReader
from . import CACHE_FILENAME


class MTKReader(DFTReader):
    def __init__(self, calculation_id, cache=True):
        self.calculation_id = calculation_id
        self.cache = True
        self._load()

    def _load(self):
        from mattoolkit.api.calculation import CalculationResourceItem

        if self.cache:
            cache_directory = os.path.expanduser('~/.cache/dftfit/')
            os.makedirs(cache_directory, exist_ok=True)
            key = f'mattoolkit.calculation.{self.calculation_id}'
            with shelve.open(os.path.join(cache_directory, CACHE_FILENAME)) as cache:
                if  key in cache:
                    calculation = cache[key]
                else:
                    calculation = CalculationResourceItem(self.calculation_id)
                    calculation.get()
                    cache[key] = calculation
        else:
            calculation = CalculationResourceItem(self.calculation_id)
            calculation.get()

        if calculation.format in {'VASP'}:
            results = calculation.results
            self._forces = np.array(results.final_forces)
            self._stress = np.array(results.final_stress) * 1e3 # kbar -> bar
            self._energy = float(results.final_energy)
            self._structure = results.final_structure
        else:
            raise ValueError('unable to use calculation type %s' % calculation.type)

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
