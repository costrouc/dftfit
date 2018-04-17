import pytest

from dftfit.io.siesta import SiestaReader


@pytest.mark.siesta
def test_siesta_reader():
    filename = 'd3_o_20ev.xml'
    directory = 'test_files/siesta'
    dftresult = SiestaReader(directory, filename)
    # test that all is well in result
