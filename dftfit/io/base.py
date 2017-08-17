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


class MDWriter:
    def write_input(self, directory):
        raise NotImplementedError()


class MDRunner:
    def run(self, writer, command, directory):
        raise NotImplementedError()

    def _run(self, command, run_directory):
        process = subprocess.Popen(command, cwd=run_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return_code = process.wait()
        stdout, stderr = process.communicate()
        return return_code, stdout, stderr
