import asyncio

import pymatgen as pmg
import numpy as np
import pytest

from dftfit.cli.utils import load_filename
from dftfit.potential import Potential

@pytest.mark.pymatgen_lammps
@pytest.mark.lammps_cython
@pytest.mark.calculator
def test_calculator_equivalency():
    from dftfit.io.lammps import LammpsLocalDFTFITCalculator
    from dftfit.io.lammps_cython import LammpsCythonDFTFITCalculator

    # Create structure
    supercell = (2, 2, 2)
    a = 4.1990858 # From evaluation of potential
    lattice = pmg.Lattice.from_parameters(a, a, a, 90, 90, 90)
    mg = pmg.Specie('Mg', 1.4)
    o = pmg.Specie('O', -1.4)
    atoms = [mg, o]
    sites = [[0, 0, 0], [0.5, 0.5, 0.5]]
    structure = pmg.Structure.from_spacegroup(225, lattice, atoms, sites)

    base_directory = 'test_files/dftfit_calculators/'
    potential_schema = load_filename(base_directory + 'potential.yaml')
    potential_schema['spec']['charge']['Mg']['initial'] = 1.6
    potential_schema['spec']['charge']['O']['initial'] = -1.6
    potential = Potential(potential_schema)

    calculators = [
        LammpsLocalDFTFITCalculator(structures=[structure], command='lammps', num_workers=1),
        LammpsCythonDFTFITCalculator(structures=[structure])
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
