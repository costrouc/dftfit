import pytest

from pymatgen import Lattice, Structure


@pytest.fixture
def structure():
    lattice = Lattice.from_parameters(4.2, 4.2, 4.2, 90, 90, 90)
    species = ['Mg', 'O']
    coordinates = [[0, 0, 0], [0.5, 0.5, 0.5]]
    return Structure(lattice, species, coordinates)
