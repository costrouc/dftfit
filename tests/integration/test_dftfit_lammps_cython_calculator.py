import pytest

from dftfit.cli.utils import load_filename
from dftfit.dftfit import dftfit
from dftfit.config import Configuration


@pytest.mark.lammps_cython
@pytest.mark.calculator
def test_lammps_cython_calculator():
    # Read in configuration information
    base_directory = 'test_files/dftfit_calculators/'
    training_schema = load_filename(base_directory + 'training.yaml')
    potential_schema = load_filename(base_directory + 'potential.yaml')
    configuration_schema = load_filename(base_directory + 'configuration.yaml')
    configuration_schema['spec']['problem'].update({
        'calculator': 'lammps_cython',
    })

    # Run optimization
    run_id = dftfit(training_schema=training_schema,
                    potential_schema=potential_schema,
                    configuration_schema=configuration_schema)

    # Ensure that the calculation ran check database
    configuration = Configuration(configuration_schema)
    with configuration.dbm.connection:
        query = configuration.dbm.connection.execute('''
        SELECT count(*) FROM evaluation WHERE run_id = ?
        ''', (run_id,)).fetchone()
        population = configuration_schema['spec']['population']
        steps = configuration_schema['spec']['steps']
        assert query[0] == population * (steps + 1) # because one initial run is done before calculation


@pytest.mark.lammps_cython
@pytest.mark.calculator
@pytest.mark.long
@pytest.mark.benchmark(min_rounds=1)
def test_lammps_cython_calculator_benchmark(benchmark):
    # Read in configuration information
    base_directory = 'test_files/dftfit_calculators/'
    training_schema = load_filename(base_directory + 'training.yaml')
    potential_schema = load_filename(base_directory + 'potential.yaml')
    configuration_schema = load_filename(base_directory + 'configuration.yaml')
    configuration_schema['spec']['problem'].update({
        'calculator': 'lammps_cython',
    })
    configuration_schema['spec']['steps'] = 3

    @benchmark
    def test_speed():
        dftfit(training_schema=training_schema,
               potential_schema=potential_schema,
               configuration_schema=configuration_schema)
