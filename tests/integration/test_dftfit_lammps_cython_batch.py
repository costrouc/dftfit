"""necisarry to test that all optimization algorithms

"""

import pytest
from unittest import mock
import random

import numpy as np

from dftfit.cli.utils import load_filename
from dftfit.dftfit import dftfit_batch


def test_lammps_cython_algorithms():
    base_directory = 'test_files/dftfit_calculators/'
    training_schema = load_filename(base_directory + 'training.yaml')
    potential_schema = load_filename(base_directory + 'potential.yaml')
    configuration_schema = load_filename(base_directory + 'configuration.yaml')
    batch_schema = load_filename('test_files/batch/example.yaml')
    configuration_schema['spec']['problem'].update({
        'calculator': 'lammps_cython',
    })

    num_features = len(configuration_schema['spec']['problem']['weights'])

    with mock.patch('dftfit.io.lammps_cython.lammps.Lammps'):
        with mock.patch('dftfit.problem.DFTFITProblemBase._fitness') as mock_fitness:
            mock_fitness.return_value = tuple(np.random.random(num_features).tolist()), random.random()
            num_jobs = dftfit_batch(training_schema=training_schema,
                                    potential_schema=potential_schema,
                                    configuration_schema=configuration_schema,
                                    batch_schema=batch_schema)
            assert num_jobs == 4
