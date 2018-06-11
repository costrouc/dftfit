import warnings

import numpy as np

from dftfit.io import VaspReader


def test_vasp_reader():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        calculation = VaspReader(
            'test_files/vasp', vasprun_filename='vasprun.xml.mgo')
    assert np.all(np.isclose(calculation.energy, -11.87675826))
    assert np.all(np.isclose(calculation.stress, np.eye(3) * -12.62984))
    assert np.all(np.isclose(calculation.forces, np.zeros((2, 3))))
    structure = calculation.structure
    assert len(structure) == 2
    assert set(s.symbol for s in structure.species) == {'Mg', 'O'}
