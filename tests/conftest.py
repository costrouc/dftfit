import pathlib

import pytest
import pymatgen as pmg

from dftfit.potential import Potential


@pytest.fixture
def structure():
    def f(filename, conventional=True, oxidized=False):
        filename = pathlib.Path(filename)
        if not filename.is_file():
            raise ValueError(f'given filename "{filename}" is not a file')

        if filename.suffix == '.cif':
            s = pmg.io.cif.CifParser(str(filename)).get_structures()[0]
        elif filename.stem == 'POSCAR':
            s = pmg.io.vasp.inputs.Poscar(str(filename)).structure
        else:
            raise ValueError(f'do not know how to convert filename {filename} to structure')

        if conventional:
            spga = pmg.symmetry.analyzer.SpacegroupAnalyzer(s)
            s = spga.get_conventional_standard_structure()

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
def mgo_structure():
    a = 4.1990858
    lattice = Lattice.from_parameters(a, a, a, 90, 90, 90)
    species = ['Mg', 'O']
    coordinates = [[0, 0, 0], [0.5, 0.5, 0.5]]
    return Structure.from_spacegroup(225, lattice, species, coordinates)
