import asyncio

import pymatgen as pmg
import numpy as np
import pytest

from dftfit.io.lammps import LammpsLocalDFTFITCalculator
from dftfit.io.lammps_cython import LammpsCythonDFTFITCalculator
from dftfit.cli.utils import load_filename
from dftfit.potential import Potential


@pytest.mark.pymatgen_lammps
@pytest.mark.lammps_cython
@pytest.mark.calculator
def test_calculator_equivalency(structure):
    target_a = 4.1990858
    s = structure('test_files/structure/MgO.cif')
    s.apply_strain(target_a / s.lattice.a - 1)
    assert np.all(np.isclose(s.lattice.abc, (target_a, target_a, target_a)))
    s = s * (2, 2, 2)
    assert len(s) == 64

    base_directory = 'test_files/dftfit_calculators/'
    potential_schema = load_filename(base_directory + 'potential.yaml')
    potential_schema['spec']['charge']['Mg']['initial'] = 1.4
    potential_schema['spec']['charge']['O']['initial'] = -1.4
    potential = Potential(potential_schema)

    calculators = [
        LammpsLocalDFTFITCalculator(structures=[s], potential=potential, command='lammps', num_workers=1),
        LammpsCythonDFTFITCalculator(structures=[s], potential=potential)
    ]

    loop = asyncio.get_event_loop()
    results = []

    async def run(calc, potential):
        await calc.create()
        return await calc.submit(potential)

    for calc in calculators:
        results.append(loop.run_until_complete(run(calc, potential)))

    assert len(results) == 2
    assert len(results[0]) == 1
    assert len(results[1]) == 1

    for r1, r2 in zip(*results):
        assert r1.structure == r2.structure
        assert abs(r1.energy - r2.energy) < 1e-4
        assert np.all(np.isclose(r1.forces, r2.forces, atol=1e-8))
        assert np.all(np.isclose(r1.stress, r2.stress, atol=1e-8))
