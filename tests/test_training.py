import pytest

from dftfit.training import Training


# mattoolkit is not running (but we will use cache to keep it alive)
@pytest.mark.mattoolkit
def test_training_mattoolkit_from_file():
    base_directory = 'test_files/training/'
    dft_calculations = Training.from_file(
        base_directory + 'training-mattoolkit-mgo.yaml',
        cache_filename="test_files/mattoolkit/cache/cache.db")
    assert len(dft_calculations.calculations) == 3


@pytest.mark.siesta
def test_training_siesta_from_filenames():
    base_directory = 'test_files/training/'
    dft_calculations = Training.from_file(
        base_directory + 'training-subset-litao3.yaml')
    assert len(dft_calculations.calculations) == 12


@pytest.mark.siesta
def test_training_siesta_from_fileglob():
    base_directory = 'test_files/training/'
    dft_calculations = Training.from_file(
        base_directory + 'training-full-litao3.yaml')
    assert len(dft_calculations.calculations) == 16
