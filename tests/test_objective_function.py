import random

import numpy as np
import pymatgen as pmg
import pytest

from dftfit.io.base import MDReader
from dftfit import objective


def create_random_reader(num_atoms):
    lattice = pmg.Lattice.from_parameters(1, 1, 1, 90, 90, 90)
    positions = np.array([(_, _, _) for _ in np.linspace(0, 1, num_atoms)])
    symbols = ['H'] * num_atoms

    return MDReader(
        energy=random.random(),
        stress=np.random.random((3, 3)),
        forces=np.random.random((num_atoms, 3)),
        structure=pmg.Structure(lattice, symbols, positions))


@pytest.mark.parametrize('objective_function', [
    objective.force_objective_function,
    objective.stress_objective_function,
    objective.energy_objective_function
])
@pytest.mark.benchmark(group='objective-function')
def test_obj_single_set_idential_calculations_fse(objective_function, benchmark):
    num_atoms = 100
    dft_sets = md_sets = [create_random_reader(num_atoms)]

    @benchmark
    def f():
        objective_function(md_sets, dft_sets)


@pytest.mark.parametrize('objective_function', [
    objective.force_objective_function,
    objective.stress_objective_function,
    objective.energy_objective_function
])
@pytest.mark.benchmark(group='objective-function')
def test_obj_100_set_idential_calculations_fse(objective_function, benchmark):
    num_atoms = 100
    num_sets = 100
    dft_sets = md_sets = [create_random_reader(num_atoms) for i in range(num_sets)]

    @benchmark
    def f():
        objective_function(md_sets, dft_sets)


@pytest.mark.parametrize('objective_function', [
    objective.force_objective_function,
    objective.stress_objective_function,
    objective.energy_objective_function
])
@pytest.mark.benchmark(group='objective-function')
def test_obj_single_set_calculations_fse(objective_function, benchmark):
    num_atoms = 100
    md_sets = [create_random_reader(num_atoms)]
    dft_sets = [create_random_reader(num_atoms)]

    @benchmark
    def f():
        objective_function(md_sets, dft_sets)


@pytest.mark.parametrize('objective_function', [
    objective.force_objective_function,
    objective.stress_objective_function,
    objective.energy_objective_function
])
@pytest.mark.benchmark(group='objective-function')
def test_obj_100_set_calculations_fse(objective_function, benchmark):
    num_atoms = 100
    num_sets = 100
    md_sets = [create_random_reader(num_atoms) for i in range(num_sets)]
    dft_sets = [create_random_reader(num_atoms) for i in range(num_sets)]

    @benchmark
    def f():
        objective_function(md_sets, dft_sets)
