import pytest

from dftfit.io import (
    read_lammps_thermo,
    read_lammps_logfile,
    read_lammps_forces_dump,
)

# Unittests for read_lammps_thermo
# LAMMPS outputs thermodynamic data at given time steps
# http://lammps.sandia.gov/doc/thermo_style.html


def test_simple_read_lammps_thermo():
    thermo_str = (
        "TotEng Pxx Pyy Pzz Pxy Pxz Pyz\n"
        "  -1.0   -2.0   -3.0   -4.0 1.0e-11 7.3e-11 6.5e+11 "
    )
    thermo_data = read_lammps_thermo(thermo_str)

    thermo_tags = ['TotEng', 'Pxx', 'Pyy', 'Pzz', 'Pxy', 'Pxz', 'Pyz']
    thermo_values = [-1.0, -2.0, -3.0, -4.0, 1.0e-11, 7.3e-11, 6.5e11]

    assert len(thermo_data) == 7
    for key, values in thermo_data.items():
        assert len(values) == 1
        assert key in thermo_tags
        assert thermo_values[thermo_tags.index(key)] == values[0]


def test_shuffled_read_lammps_thermo():
    thermo_str = (
        "Pzz TotEng Pyy Pxz Pxy Pxx Pyz\n"
        "  -1.0   -2.0   -3.0   -4.0 1.0e-11 7.3e-11 6.5e+11 "
    )
    thermo_data = read_lammps_thermo(thermo_str)

    thermo_tags = ['Pzz', 'TotEng', 'Pyy', 'Pxz', 'Pxy', 'Pxx', 'Pyz']
    thermo_values = [-1.0, -2.0, -3.0, -4.0, 1.0e-11, 7.3e-11, 6.5e11]

    assert len(thermo_data) == 7
    for key, values in thermo_data.items():
        assert len(values) == 1
        assert key in thermo_tags
        assert thermo_values[thermo_tags.index(key)] == values[0]


def test_additional_tags_read_lammps_thermo():
    thermo_str = (
        "TotEng Pzz Step Pyy Pxx Pxy Pxz Pyz Cella Cellb \n"
        "  -681.47773   -40340.424        0   -40340.424   -40340.424 2.8762538e-11 7.3760285e-11 6.5723781e-11    8.4697248    8.4697248 "
    )
    thermo_data = read_lammps_thermo(thermo_str)

    thermo_tags = ['TotEng', 'Pzz', 'Pyy', 'Pxx', 'Pxy', 'Pxz', 'Pyz']
    thermo_values = [-681.47773, -40340.424, -40340.424, -40340.424, 2.8762538e-11, 7.3760285e-11, 6.5723781e-11]

    assert len(thermo_data) == 7
    for key, values in thermo_data.items():
        assert len(values) == 1
        assert key in thermo_tags
        assert thermo_values[thermo_tags.index(key)] == values[0]


def test_missing_tag_read_lammps_thermo():
    thermo_str = (
        "Pzz TotEng Pxz Pxy Pxx Pyz\n"
        "  -1.0      -3.0   -4.0 1.0e-11 7.3e-11 6.5e+11 "
    )
    with pytest.raises(Exception) as excinfo:
        read_lammps_thermo(thermo_str)
    assert (
        "Thermo style must include "
        "['TotEng', 'Pxx', 'Pyy', 'Pzz', 'Pxy', 'Pxz', 'Pyz']"
    ) == str(excinfo.value)


def test_incorrect_tags_read_lammps_thermo():
    thermo_str = (
        "Step Temp E_pair E_mol TotEng Press \n"
        "     0          0.1    -21297.33            0   -21297.304    -98882.15 "
    )
    with pytest.raises(Exception) as excinfo:
        read_lammps_thermo(thermo_str)
    assert (
        "Thermo style must include "
        "['TotEng', 'Pxx', 'Pyy', 'Pzz', 'Pxy', 'Pxz', 'Pyz']"
    ) == str(excinfo.value)


# Unittests for read_lammps_logfile
# http://lammps.sandia.gov/doc/log.html
def test_empty_file_read_lammps_logfile():
    with pytest.raises(Exception) as excinfo:
        read_lammps_logfile("data/lammps/log/log.lammps.3")
    assert "Unable to read thermo data from logfile" == str(excinfo.value)


# Unittest for read_lammps_forces_dump
# http://lammps.sandia.gov/doc/dump.html
def test_empty_file_read_lammps_forces_dump():
    filename = "data/lammps/forces/empty.forces"
    with pytest.raises(ValueError) as excinfo:
        data = read_lammps_forces_dump(filename)
    assert "Unable to read forces from {}".format(filename) == str(excinfo.value)


def test_correct_read_lammps_forces_dump():
    filename = "data/lammps/forces/mgo.forces"
    forces = read_lammps_forces_dump(filename)
    assert len(forces) == 64
