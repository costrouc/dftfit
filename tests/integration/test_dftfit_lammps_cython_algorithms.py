"""necisarry to test that all optimization algorithms

"""

import pytest
from unittest.mock import patch
import random

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
        def __init__(self, potential, training, features, *args, **kwargs):
            self.potential = potential
            self.features = features

        def store_evaluation(self, potential, errors, value):
            pass

        def _fitness(self, paramters):
            errors = tuple(np.random.random(len(self.features)).tolist())
            value = random.random()
            return errors, value

        def __deepcopy__(self, memo):
            return self # override copy method

        def finalize(self):
            pass

        def __del__(self):
            pass

        def get_bounds(self):
            return tuple(zip(*self.potential.optimization_bounds.tolist()))

    with patch('dftfit.problem.DFTFITProblemBase', new=MockProblem):
        run_id = dftfit(training_schema=training_schema,
                        potential_schema=potential_schema,
                        configuration_schema=configuration_schema)
