import pytest

from dftfit.training import Training


# mattoolkit is not running (but we will use cache to keep it alive)
@pytest.mark.mattoolkit
def test_potential_from_file():
    base_directory = 'test_files/training/'
    Training.from_file(
        base_directory + 'training-mattoolkit-mgo.yaml',
        cache_filename=base_directory + "/cache/cache.db")
