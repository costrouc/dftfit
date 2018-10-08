import pathlib

import pytest
import pymatgen as pmg
from pymatgen.io.cif import CifParser

from dftfit.potential import Potential
from dftfit.training import Training


@pytest.fixture
def structure():
    def f(filename, conventional=True, oxidized=False):
        filename = pathlib.Path(filename)
        if not filename.is_file():
            raise ValueError(f'given filename "{filename}" is not a file')

        if filename.suffix == '.cif':
            s = CifParser(str(filename)).get_structures(primitive=(not conventional))[0]
        elif filename.stem == 'POSCAR':
            s = pmg.io.vasp.inputs.Poscar(str(filename)).structure
        else:
            raise ValueError(f'do not know how to convert filename {filename} to structure')

        if not oxidized:
            s.remove_oxidation_states()

        return s
    return f


@pytest.fixture
def potential():
    def f(filename, format=None):
        return Potential.from_file(filename, format=format)
    return f


@pytest.fixture
def training():
    def f(filename, format=None, cache_filename=None):
        return Training.from_file(filename, format=format, cache_filename=cache_filename)
    return f


@pytest.fixture
def mgo_structure():
    a = 4.1990858
    lattice = Lattice.from_parameters(a, a, a, 90, 90, 90)
    species = ['Mg', 'O']
    coordinates = [[0, 0, 0], [0.5, 0.5, 0.5]]
    return Structure.from_spacegroup(225, lattice, species, coordinates)
