import pytest

import pymatgen as pmg


@pytest.mark.benchmark
def test_potential_buck_charge(benchmark, structure):
    s = structure('test_files/structure/MgO.cif') * (2, 2, 2)

    # get time for construction
