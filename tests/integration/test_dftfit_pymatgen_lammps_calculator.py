import pytest

from dftfit.cli.utils import load_filename
from dftfit.dftfit import dftfit
from dftfit.config import Configuration


@pytest.mark.pymatgen_lammps
def test_pymatgen_lammps_calculator():
    # Read in configuration information
    base_directory = 'test_files/dftfit_calculators/'
    training_schema = load_filename(base_directory + 'training.yaml')
    potential_schema = load_filename(base_directory + 'potential.yaml')
    configuration_schema = load_filename(base_directory + 'configuration.yaml')
    configuration_schema['spec']['problem'].update({
        'calculator': 'lammps',
        'command': 'lammps',
        'num_workers': 2
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
