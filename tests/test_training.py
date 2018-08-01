import pytest

from dftfit.training import Training


# mattoolkit is not running (but we will use cache to keep it alive)
@pytest.mark.parametrize('filename, num_calculations, material_properties', [
    ('training-mattoolkit-mgo.yaml', 3, set()),
    ('training-subset-litao3.yaml', 12, set()),
    ('training-full-litao3.yaml', 16, set()),
    ('training-mattoolkit-mgo-properties.yaml', 3, {'lattice_constants', 'elastic_constants', 'bulk_modulus', 'shear_modulus'}),
])
def test_training_from_file(filename, num_calculations, material_properties):
    kwargs = {}
    if 'mattoolkit' in filename:
        kwargs = {'cache_filename': "test_files/mattoolkit/cache/cache.db"}

    training = Training.from_file('test_files/training/%s' % filename, **kwargs)
    assert len(training.calculations) == num_calculations
    assert set(training.material_properties.keys()) == material_properties
