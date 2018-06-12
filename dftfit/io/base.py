import subprocess


class DFTReader:
    @property
    def forces(self):
        """ return numpy.ndarray X x 3 in units [eV/Angstom] """
        raise NotImplementedError()

    @property
    def stress(self):
        """ return numpy.ndarray 3 x 3 in units [GPa] """
        raise NotImplementedError()

    @property
    def energy(self):
        """ return float in units [eV] """
        raise NotImplementedError()

    @property
    def structure(self):
        """ returns pymatgen.Structure. Not units for pymatgen are Angstroms """
        raise NotImplementedError()


class MDReader:
    def __init__(self, forces, stress, energy, structure):
        self._forces = forces
        self._stress = stress
        self._energy = energy
        self._structure = structure

    @property
    def forces(self):
        """ return numpy.ndarray X x 3 in units [eV/Angstom] """
        return self._forces

    @property
    def stress(self):
        """ return numpy.ndarray 3 x 3 in units [GPa] """
        return self._stress

    @property
    def energy(self):
        """ return float in units [eV] """
        return self._energy

    @property
    def structure(self):
        """ returns pymatgen.Structure. Not units for pymatgen are Angstroms """
        return self._structure


class DFTFITCalculator:
    """DFTFIT interface. Should have a simple api. Only `__init__`
    interface may change.

    """
    def __init__(self, structures):
        raise NotImplementedError()

    async def create(self):
        raise NotImplementedError()

    async def submit(self, potential, properties=None):
        properties = properties or {'stress', 'energy', 'forces'}
        raise NotImplementedError()


class MDCalculator:
    async def submit(self, structure, potential):
        raise NotImplementedError()
