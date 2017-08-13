import pytest

from pymatgen import Lattice, Structure


@pytest.fixture
def mgo_structure():
    a = 4.1990858
    lattice = Lattice.from_parameters(a, a, a, 90, 90, 90)
    species = ['Mg', 'O']
    coordinates = [[0, 0, 0], [0.5, 0.5, 0.5]]
    return Structure.from_spacegroup(225, lattice, species, coordinates)
