from dftfit.cli.utils import load_filename
from dftfit.dftfit import dftfit

base_directory = 'test_files/dftfit_calculators/'
training_schema = load_filename(base_directory + 'training.yaml')
potential_schema = load_filename(base_directory + 'potential.yaml')
configuration_schema = load_filename(base_directory + 'configuration.yaml')
configuration_schema['spec']['problem'].update({
    'calculator': 'lammps_cython',
})
configuration_schema['spec']['steps'] = 100

run_id = dftfit(training_schema=training_schema,
                potential_schema=potential_schema,
                configuration_schema=configuration_schema)
