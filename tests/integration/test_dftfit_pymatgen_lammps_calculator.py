import pytest

from dftfit.cli.utils import load_filename
from dftfit.dftfit import dftfit


@pytest.mark.pymatgen_lammps
def test_pymatgen_lammps_calculator():
    base_directory = 'test_files/dftfit_calculators/pymatgen_lammps/'
    training_schema = load_filename(
        base_directory + 'training.yaml')
    potential_schema = load_filename(
        base_directory + 'potential.yaml')
    configuration_schema = load_filename(
        base_directory + 'configuration.yaml')

    dftfit(training_schema=training_schema,
           potential_schema=potential_schema,
           configuration_schema=configuration_schema)
