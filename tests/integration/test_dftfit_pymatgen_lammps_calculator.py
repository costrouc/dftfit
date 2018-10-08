import pytest
import shutil

from dftfit.cli.utils import load_filename
from dftfit.dftfit import dftfit
from dftfit.config import Configuration


@pytest.mark.pymatgen_lammps
@pytest.mark.calculator
def test_pymatgen_lammps_calculator():
    # Read in configuration information
    base_directory = 'test_files/dftfit_calculators/'
    training_schema = load_filename(base_directory + 'training.yaml')
    potential_schema = load_filename(base_directory + 'potential.yaml')
    configuration_schema = load_filename(base_directory + 'configuration.yaml')

    command = None
    if shutil.which('lammps'): command = 'lammps'
    elif shutil.which('lmp_serial'): command = 'lmp_serial'

    configuration_schema['spec']['problem'].update({
        'calculator': 'lammps',
        'command': command,
        'num_workers': 1
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
        # because one initial run is done before calculation
        assert query[0] == configuration.population * (configuration.steps + 1)


@pytest.mark.pymatgen_lammps
@pytest.mark.calculator
@pytest.mark.long
@pytest.mark.benchmark(group='calculators', min_rounds=1)
def test_pymatgen_lammps_calculator_benchmark(benchmark):
    # Read in configuration information
    base_directory = 'test_files/dftfit_calculators/'
    training_schema = load_filename(base_directory + 'training.yaml')
    potential_schema = load_filename(base_directory + 'potential.yaml')
    configuration_schema = load_filename(base_directory + 'configuration.yaml')
    configuration_schema['spec']['problem'].update({
        'calculator': 'lammps',
        'command': 'lammps',
        'num_workers': 1,
    })
    configuration_schema['spec']['steps'] = 3

    @benchmark
    def test_speed():
        dftfit(training_schema=training_schema,
               potential_schema=potential_schema,
               configuration_schema=configuration_schema)
