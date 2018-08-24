"""necisarry to test that all optimization algorithms

"""

import pytest
from unittest import mock
import random

import numpy as np

from dftfit.cli.utils import load_filename
from dftfit.dftfit import dftfit



@pytest.mark.parametrize('algorithm', [
    'pygmo.sade',
    'pygmo.de1220',
    'pygmo.pso',
    'pygmo.sea',
    'pygmo.sga',
    'pygmo.bee_colony',
    # 'pygmo.cmaes',
    'pygmo.nsga2',
    # 'pygmo.moead'
    'nlopt.cobyla',
    'nlopt.bobyqa',
    'nlopt.newuoa',
    'nlopt.sbplx'
])
def test_lammps_cython_algorithms(algorithm):
    base_directory = 'test_files/dftfit_calculators/'
    training_schema = load_filename(base_directory + 'training.yaml')
    potential_schema = load_filename(base_directory + 'potential.yaml')
    configuration_schema = load_filename(base_directory + 'configuration.yaml')
    configuration_schema['spec']['problem'].update({
        'calculator': 'lammps_cython',
    })

    # do bare minimum calculations
    configuration_schema['spec']['algorithm'].update({
        'name': algorithm,
        'steps': 1,
        # Local optimization methods only opperate on one value
        'population': 1 if 'nlopt' in algorithm else 8
    })

    # Run optimization with mocked python evaulation
    class MockProblem:
        def __getattr__(self, *args, **kwargs):
            raise ValueError()

    num_features = len(configuration_schema['spec']['problem']['weights'])

    with mock.patch('dftfit.io.lammps_cython.lammps.Lammps'):
        with mock.patch('dftfit.problem.DFTFITProblemBase._fitness') as mock_fitness:
            mock_fitness.return_value = tuple(np.random.random(num_features).tolist()), random.random()
            run_id = dftfit(training_schema=training_schema,
                            potential_schema=potential_schema,
                            configuration_schema=configuration_schema)
