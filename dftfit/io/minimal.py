from .base import MDReader


class MinimalMDReader(MDReader):
    def __init__(self, forces, stress, energy, structure):
        self._forces = forces
        self._stress = stress
        self._energy = energy
        self._structure = structure

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
