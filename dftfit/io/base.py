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


# Need MDPotential class


class MDWriter:
    def write_input(self, directory):
        raise NotImplementedError()
