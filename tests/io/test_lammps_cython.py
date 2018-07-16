import asyncio

import pytest

from dftfit.io.lammps_cython import LammpsCythonDFTFITCalculator


@pytest.mark.parametrize('structure_filename, supercell, num_atoms, potential_filename', [
    ('MgO.cif', (2, 2, 2), 64, 'MgO-charge-buck-fitting.yaml'),     # buckingham
    ('LiTaO3.cif', (1, 1, 1), 30, 'LiTaO3-tersoff-2.yaml'),         # tersoff-2
    ('LiTaO3.cif', (1, 1, 1), 30, 'LiTaO3-tersoff-2-charge.yaml'),  # tersoff-2 + charge
    ('3C-SiC.cif', (2, 2, 2), 64, 'SiC-gao-weber.yaml'),            # gao-weber
    ('3C-SiC.cif', (2, 2, 2), 64, 'SiC-tersoff.yaml'),              # tersoff
    ('CdTe.cif', (2, 2, 2), 64, 'CdTe-stillinger-weber.yaml'),      # stillinger-weber
])
@pytest.mark.benchmark(group='apply-potential', min_rounds=10)
def test_potential_lammps_cython(
        benchmark, structure, potential,
        structure_filename, supercell, num_atoms, potential_filename):
    s = structure('test_files/structure/%s' % structure_filename) * supercell
    assert len(s) == num_atoms
    p = potential('test_files/potential/%s' % potential_filename)

    calculator = LammpsCythonDFTFITCalculator([s])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(calculator.create())

    # using calculator internals
    lmp = calculator.lammps_systems[-1]

    @benchmark
    def f():
        calculator._apply_potential_files(p)
        calculator._apply_potential(lmp, p)
