import asyncio

import pytest
import pymatgen as pmg

from dftfit.io.lammps_cython import LammpsCythonDFTFITCalculator


@pytest.mark.benchmark(group='apply-potential', min_rounds=10)
def test_potential_buck_charge(benchmark, structure, potential):
    s = structure('test_files/structure/MgO.cif') * (2, 2, 2)
    p = potential('test_files/potential/mgo-fitting.yaml')

    calculator = LammpsCythonDFTFITCalculator([s])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(calculator.create())

    # using calculator internals
    lmp = calculator.lammps_systems[-1]

    @benchmark
    def f():
        calculator._apply_potential(lmp, p)
