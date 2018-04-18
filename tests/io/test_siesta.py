import pytest

import numpy as np

from dftfit.io.siesta import SiestaReader


@pytest.mark.siesta
def test_siesta_reader():
    filename = 'd3_o_20ev.xml'
    directory = 'test_files/siesta'
    calculation = SiestaReader(directory, filename)
    assert np.all(np.isclose(calculation.energy, -104742.133616))

    first_row_forces = np.array([-5.014637520260e-1, -4.224890317363e-1, -1.420257672235e-1])
    assert np.all(np.isclose(calculation.forces[0], first_row_forces))

    eVA32GPa = 160.21766208 # http://greif.geo.berkeley.edu/~driver/conversions.html
    stresses = np.array([
        [-2.765925809224e-3, -3.009750267323e-5, 1.171322722617e-4],
        [-2.908082457191e-5, -3.180769833963e-3, -1.264574964357e-4],
        [1.174490293284e-4, -1.258277686581e-4, -1.767562635815e-3]
    ]) * eVA32GPa
    assert np.all(np.isclose(calculation.stress, stresses))
