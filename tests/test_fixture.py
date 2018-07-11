import pymatgen as pmg


def test_structure_fixture_conventional(structure):
    s = structure('test_files/structure/MgO.cif', conventional=True)
    assert isinstance(s, pmg.Structure)
    assert len(s) == 8


def test_structure_fixture_primitive(structure):
    s = structure('test_files/structure/MgO.cif', conventional=False)
    assert isinstance(s, pmg.Structure)
    assert len(s) == 2
