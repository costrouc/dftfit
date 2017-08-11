import numpy as np


class Dftfit:
    """ DFT Fitting calculations

    Arguments:


    """

    MD_SOLVERS = {'LAMMPS'}

    def __init__(self, max_iter=-1, step_toll=1e-6, w_f=0.8, w_s=0.1, w_e=0.1):
        self.max_iter = max_iter
        self.step_toll = step_toll

        if not np.isclose(sum(w_f, w_s, w_e), 1.0, 1e-8):
            raise ValueError('sum of weighting functions must be one')

        self.weights = {
            'forces': w_f,
            'stress': w_s,
            'energy': w_e
        }


    def fit(self, dft_calculations, starting_potential):
        """

        """
        pass


    def predict(self, structure):
        pass
