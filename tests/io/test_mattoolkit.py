import pytest
import numpy as np

from dftfit.io.mattoolkit import MTKReader

# I don't really have plans to make mattoolkit available in the future
# @pytest.mark.mattoolkit
# def test_mattoolkit():
#     mtk = MTKReader(2) # super relaxation
#     assert np.all(np.isclose(mtk.forces, np.zeros((8, 3))))
#     assert np.all(np.isclose(mtk.stress, np.eye(3) * -36.97713))
#     assert np.isclose(mtk.energy, -47.47590796)
#     structure = mtk.structure
#     assert len(structure) == 8
#     assert set(s.symbol for s in structure.species) == {'Mg', 'O'}
