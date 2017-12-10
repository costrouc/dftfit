import shelve
import os

import numpy as np

from .base import DFTReader
from ..config import CACHE_FILENAME


class MTKReader(DFTReader):
    def __init__(self, calculation_id, use_cache=True):
        self.calculation_id = calculation_id
        self._load(use_cache=use_cache)

    def _download(self, calculation_id):
        from mattoolkit.api.calculation import CalculationResourceItem

        calculation = CalculationResourceItem(calculation_id)
        calculation.get()

        if calculation.format in {'VASP'}:
            results = calculation.results
            return {
                'forces': np.array(results.final_forces),
                'stress': np.array(results.final_stress) * 1e3, # kbar -> bar
                'energy': float(results.final_energy),
                'structure': results.final_structure
            }
        else:
            raise ValueError('unable to use calculation type %s' % calculation.type)

    def _load(self, use_cache):
        if use_cache:
            cache_directory = os.path.expanduser('~/.cache/dftfit/')
            os.makedirs(cache_directory, exist_ok=True)
            key = f'mattoolkit.calculation.{self.calculation_id}'
            with shelve.open(os.path.join(cache_directory, CACHE_FILENAME)) as cache:
                if key in cache:
                    results = cache[key]
                else:
                    results = self._download(self.calculation_id)
                    cache[key] = results
        else:
            results = self._download(self.calculation_id)

        self._forces = results['forces']
        self._stress = results['stress']
        self._energy = results['energy']
        self._structure = results['structure']

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
