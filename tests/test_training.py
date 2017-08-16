import pytest

from dftfit.training import Training


@pytest.mark.mattoolkit
def test_potential_from_file():
    potential = Training.from_file('test_files/training/training-mgo.yaml')
