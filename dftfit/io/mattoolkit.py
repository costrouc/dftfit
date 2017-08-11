from .base import DFTReader

import numpy as np


class MTKReader(DFTReader):
    def __init__(self, calculation_id):
        self.calculation_id = calculation_id
        self._load()

    def _load(self):
        from mattoolkit.api.calculation import CalculationResourceItem
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
