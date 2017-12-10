from tempfile import TemporaryDirectory
import os

import numpy as np
from pymatgen import Lattice, Specie, Structure

from dftfit.io import LammpsReader


def test_lammps_reader():
    lammps = LammpsReader('test_files/lammps/mgo')
    assert np.all(np.isclose(lammps.forces, np.zeros((8, 3))))
    assert np.all(np.isclose(lammps.stress, np.eye(3) * 661.01685))
    assert np.isclose(lammps.energy, -85.34101)
    structure = lammps.structure
    assert len(structure) == 8
    assert set(s.symbol for s in structure.species) == {'Mg', 'O'}



# def test_lammps_writer():
#     supercell = (5, 5, 5)
#     a = 4.1990858 # From evaluation of potential
#     lattice = Lattice.from_parameters(a, a, a, 90, 90, 90)
#     mg = Specie('Mg', 1.4)
#     o = Specie('O', -1.4)
#     atoms = [mg, o]
#     sites = [[0, 0, 0], [0.5, 0.5, 0.5]]
#     structure = Structure.from_spacegroup(225, lattice, atoms, sites)

#     potential_schema = {
#         'version': 'v1',
#         'kind': 'Potential',
#         'spec': {
#             'charge': {
#                 'Mg': 1.4, 'O': -1.4
#             },
#             'kspace': {
#                 'type': 'pppm', 'tollerance': 1e-5
#             },
#             'pair': {
#                 'type': 'buckingham',
#                 'cutoff': 10.0,
#                 'parameters': [
#                     {
#                         'elements': ['Mg', 'Mg'],
#                         'coefficients': [1309362.2766468062, 0.104, 0.0]
#                     },
#                     {
#                         'elements': ['Mg', 'O'],
#                         'coefficients': [9892.357, 0.20199, 0.0]
#                     },
#                     {
#                         'elements': ['O', 'O'],
#                         'coefficients': [2145.7345, 0.3, 30.2222]
#                     }
#                 ]
#             }
#         }
#     }

#     lammps = LammpsWriter(structure, potential_schema)
#     with TemporaryDirectory() as tempdir:
#         lammps.write_input(tempdir)
#         assert set(os.listdir(tempdir)) == {'lammps.in', 'initial.data'}
