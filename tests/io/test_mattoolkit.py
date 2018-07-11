import pytest
import numpy as np

from dftfit.io.mattoolkit import MTKReader

# We use the cache since REST api no longer available
@pytest.mark.mattoolkit
def test_mattoolkit():
    cache_filename = 'test_files/mattoolkit/cache/cache.db'
    mtk = MTKReader(2, cache_filename=cache_filename) # super relaxation
    assert np.all(np.isclose(mtk.forces, np.zeros((8, 3))))
    assert np.all(np.isclose(mtk.stress, np.eye(3) * -36.97713))
    assert np.isclose(mtk.energy, -47.47590796)
    structure = mtk.structure
    assert len(structure) == 8
    assert set(s.symbol for s in structure.species) == {'Mg', 'O'}
