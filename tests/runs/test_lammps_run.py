import pytest
from pymatgen import Structure, Lattice, Specie
import numpy as np

from dftfit.io.lammps import LammpsWriter, LammpsRunner
from dftfit.potential import Potential


@pytest.mark.lammps
def test_lammps_run_valid(mgo_structure):
    structure = mgo_structure * (5, 5, 5) # 1000 = 125 * 8
    potential = Potential.from_file('test_files/potential/mgo.yaml')

    writer = LammpsWriter(structure, potential)
    reader = LammpsRunner().run(writer, ['lammps', '-i', 'lammps.in'], '/tmp/lammps')
    assert np.all(np.isclose(reader.forces, np.zeros((1000, 3))))
    assert np.all(np.isclose(reader.stress, np.eye(3) *  6.10545970e+02))
    assert np.isclose(reader.energy, -10667.662)
    structure = reader.structure
    assert len(structure) == 1000
    assert set(s.symbol for s in structure.species) == {'Mg', 'O'}
