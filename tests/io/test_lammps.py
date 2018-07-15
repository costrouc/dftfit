from collections import OrderedDict

import numpy as np
import pymatgen as pmg

import pytest
from pmg_lammps import LammpsInput, LammpsData, LammpsScript

from dftfit.potential import Potential
from dftfit.io.lammps import (
    LammpsReader, lammps_dftfit_set, modify_input_for_potential
)


@pytest.mark.pymatgen_lammps
@pytest.mark.calculator
def test_lammps_reader():
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
def test_lammps_writer_buckingham(structure, potential):
    """Tests that given a structure and potential that a certain lammps
    input script is created.

    """
    s = structure('test_files/structure/MgO.cif', conventional=True) * (2, 2, 2)
    assert len(s) == 64

    p = potential('test_files/potential/MgO-charge-buck.yaml')

    lammps_input = LammpsInput(
        LammpsScript(lammps_dftfit_set),
        LammpsData.from_structure(s))
    modify_input_for_potential(lammps_input, p)

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
