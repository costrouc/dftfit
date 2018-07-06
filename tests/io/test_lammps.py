from collections import OrderedDict

import numpy as np
from pymatgen import Lattice, Specie, Structure
import pytest

from dftfit.potential import Potential

@pytest.mark.pymatgen_lammps
@pytest.mark.calculator
def test_lammps_reader():
    from pmg_lammps import LammpsInput, LammpsData, LammpsScript
    from dftfit.io.lammps import (
        LammpsReader, lammps_dftfit_set, modify_input_for_potential
    )

    base_directory = 'test_files/lammps/'
    lammps = LammpsReader(base_directory + 'mgo')
    assert np.all(np.isclose(lammps.forces, np.zeros((8, 3))))
    assert np.all(np.isclose(lammps.stress, np.eye(3) * 661.01685))
    assert np.isclose(lammps.energy, -85.34101)
    structure = lammps.structure
    assert len(structure) == 8
    assert set(s.symbol for s in structure.species) == {'Mg', 'O'}

@pytest.mark.pymatgen_lammps
@pytest.mark.calculator
def test_lammps_writer_buckingham():
    """Tests that given a structure and potential that a certain lammps
    input script is created.

    """
    from pmg_lammps import LammpsInput, LammpsData, LammpsScript
    from dftfit.io.lammps import (
        LammpsReader, lammps_dftfit_set, modify_input_for_potential
    )

    # Create structure
    supercell = (2, 2, 2)
    a = 4.1990858 # From evaluation of potential
    lattice = Lattice.from_parameters(a, a, a, 90, 90, 90)
    mg = Specie('Mg', 1.4)
    o = Specie('O', -1.4)
    atoms = [mg, o]
    sites = [[0, 0, 0], [0.5, 0.5, 0.5]]
    structure = Structure.from_spacegroup(225, lattice, atoms, sites)

    # Create Potential
    potential = Potential({
        'version': 'v1',
        'kind': 'Potential',
        'spec': {
            'charge': {
                'Mg': 1.4, 'O': -1.4
            },
            'kspace': {
                'type': 'pppm', 'tollerance': 1e-5
            },
            'pair': {
                'type': 'buckingham',
                'cutoff': 10.0,
                'parameters': [
                    {
                        'elements': ['Mg', 'Mg'],
                        'coefficients': [1309362.2766468062, 0.104, 0.0]
                    },
                    {
                        'elements': ['Mg', 'O'],
                        'coefficients': [9892.357, 0.20199, 0.0]
                    },
                    {
                        'elements': ['O', 'O'],
                        'coefficients': [2145.7345, 0.3, 30.2222]
                    }
                ]
            }
        }
    })

    lammps_input = LammpsInput(
        LammpsScript(lammps_dftfit_set),
        LammpsData.from_structure(structure))
    modify_input_for_potential(lammps_input, potential)

    output_script = [
        ('echo', 'both'),
        ('log', 'lammps.log'),
        ('units', 'metal'),
        ('dimension', 3),
        ('boundary', 'p p p'),
        ('atom_style', 'full'),
        ('read_data', 'initial.data'),
        ('kspace_style', 'pppm 0.000010'),
        ('pair_style', 'buck/coul/long 10.0'),
        ('pair_coeff', [
            '1 1 1309362.2766468062 0.104 0.0',
            '1 2 9892.357 0.20199 0.0',
            '2 2 2145.7345 0.3 30.2222'
        ]),
        ('set', [
            'type 1 charge 1.400000',
            'type 2 charge -1.400000',
        ]),
        ('dump', '1 all custom 1 mol.lammpstrj id type x y z fx fy fz'),
        ('dump_modify', '1 sort id'),
        ('thermo_modify', 'flush yes'),
        ('thermo_style', 'custom step etotal pxx pyy pzz pxy pxz pyz'),
        ('run', 0)
    ]
    assert OrderedDict(output_script) == lammps_input.lammps_script
