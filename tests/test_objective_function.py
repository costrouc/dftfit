import random

import numpy as np
import pymatgen as pmg
import pytest

from dftfit.io.base import MDReader
from dftfit.problem import multiobjective_function, singleobjective_function


def create_random_reader(num_atoms):
    lattice = pmg.Lattice.from_parameters(1, 1, 1, 90, 90, 90)
    positions = np.array([(_, _, _) for _ in np.linspace(0, 1, num_atoms)])
    symbols = ['H'] * num_atoms

    return MDReader(
        energy=random.random(),
        stress=np.random.random((3, 3)),
        forces=np.random.random((num_atoms, 3)),
        structure=pmg.Structure(lattice, symbols, positions))


def test_singleobj_single_set_idential_calculations_fse(benchmark):
    num_atoms = 100
    dft_sets = md_sets = [create_random_reader(num_atoms)]
    weights = {'forces': 1/3, 'stress': 1/3, 'energy': 1/3}

    @benchmark
    def f():
        singleobjective_function(md_sets, dft_sets, weights)


def test_singleobj_100_set_idential_calculations_fse(benchmark):
    num_atoms = 100
    num_sets = 100
    dft_sets = md_sets = [create_random_reader(num_atoms) for i in range(num_sets)]
    weights = {'forces': 1/3, 'stress': 1/3, 'energy': 1/3}

    @benchmark
    def f():
        singleobjective_function(md_sets, dft_sets, weights)


@pytest.mark.benchmark(group='objective-function')
def test_singleobj_single_set_calculations_fse(benchmark):
    num_atoms = 100
    md_sets = [create_random_reader(num_atoms)]
    dft_sets = [create_random_reader(num_atoms)]
    weights = {'forces': 1/3, 'stress': 1/3, 'energy': 1/3}

    @benchmark
    def f():
        singleobjective_function(md_sets, dft_sets, weights)


@pytest.mark.benchmark(group='objective-function')
def test_singleobj_single_set_calculations_fse(benchmark):
    num_atoms = 100
    md_sets = [create_random_reader(num_atoms)]
    dft_sets = [create_random_reader(num_atoms)]
    weights = {'forces': 1/3, 'stress': 1/3, 'energy': 1/3}

    @benchmark
    def f():
        singleobjective_function(md_sets, dft_sets, weights)


@pytest.mark.benchmark(group='objective-function')
def test_multiobj_single_set_calculations_fse(benchmark):
    num_atoms = 100
    md_sets = [create_random_reader(num_atoms)]
    dft_sets = [create_random_reader(num_atoms)]

    @benchmark
    def f():
        multiobjective_function(md_sets, dft_sets)


@pytest.mark.benchmark(group='objective-function')
def test_singleobj_100_set_calculations_fse(benchmark):
    num_atoms = 100
    num_sets = 100
    md_sets = [create_random_reader(num_atoms) for i in range(num_sets)]
    dft_sets = [create_random_reader(num_atoms) for i in range(num_sets)]
    weights = {'forces': 1/3, 'stress': 1/3, 'energy': 1/3}

    @benchmark
    def f():
        singleobjective_function(md_sets, dft_sets, weights)


@pytest.mark.benchmark(group='objective-function')
def test_multiobj_100_set_calculations_fse(benchmark):
    num_atoms = 100
    num_sets = 100

    md_sets = [create_random_reader(num_atoms) for i in range(num_sets)]
    dft_sets = [create_random_reader(num_atoms) for i in range(num_sets)]

    @benchmark
    def f():
        multiobjective_function(md_sets, dft_sets)
