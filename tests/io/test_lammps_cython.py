import asyncio

import pytest
import pymatgen as pmg

from dftfit.io.lammps_cython import LammpsCythonDFTFITCalculator


@pytest.mark.benchmark(group='apply-potential', min_rounds=10)
def test_potential_lammps_cython_buck_charge(benchmark, structure, potential):
    s = structure('test_files/structure/MgO.cif') * (2, 2, 2)
    p = potential('test_files/potential/MgO-charge-buck-fitting.yaml')

    calculator = LammpsCythonDFTFITCalculator([s])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(calculator.create())

    # using calculator internals
    lmp = calculator.lammps_systems[-1]

    @benchmark
    def f():
        calculator._apply_potential(lmp, p)


@pytest.mark.benchmark(group='apply-potential', min_rounds=10)
def test_potential_lammps_cython_tersoff_2_file(benchmark, structure, potential):
    s = structure('test_files/structure/LiTaO3.cif', conventional=True)
    assert len(s) == 30

    p = potential('test_files/potential/LiTaO3-tersoff-2.yaml')

    calculator = LammpsCythonDFTFITCalculator([s])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(calculator.create())

    # using calculator internals
    lmp = calculator.lammps_systems[-1]

    @benchmark
    def f():
        calculator._apply_potential_files(p)


@pytest.mark.benchmark(group='apply-potential', min_rounds=10)
def test_potential_lammps_cython_tersoff_2_potential(benchmark, structure, potential):
    s = structure('test_files/structure/LiTaO3.cif', conventional=True)
    assert len(s) == 30

    p = potential('test_files/potential/LiTaO3-tersoff-2.yaml')

    calculator = LammpsCythonDFTFITCalculator([s])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(calculator.create())

    # using calculator internals
    lmp = calculator.lammps_systems[-1]
    calculator._apply_potential_files(p)

    @benchmark
    def f():
        calculator._apply_potential(lmp, p)
