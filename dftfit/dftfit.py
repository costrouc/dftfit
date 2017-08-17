import numpy as np
from scipy import optimize

from ._optimize import evaluate, optimize_function


class Dftfit:
    """ DFT Fitting calculations

    Arguments:


    """

    MD_SOLVERS = {'LAMMPS'}

    def __init__(self,
                 weight_forces=0.8, weight_stress=0.1, weight_energy=0.1,
                 max_iterations=100, step_tolerance=1e-6,  method="L-BFGS-B"):
        self.max_iterations = max_iterations
        self.step_tolerance = step_tolerance
        self.method = method

        if not np.isclose(sum([weight_forces, weight_stress, weight_energy]), 1.0, 1e-8):
            raise ValueError('sum of weighting functions must be one')

        self.weights = {
            'forces': weight_forces,
            'stress': weight_stress,
            'energy': weight_energy
        }


    def fit(self, calculations, initial_potential):
        """

        Args:
           - calculations: training set of DFT calculations to fit
           - potential: model of Potential to fit
        """
        def optimization_function(parameters):
            potential = initial_potential.copy()
            potential.optimization_parameters = parameters
            md_calculations = []

            for calculation in calculations:
                md_calculation = evaluate('LAMMPS', calculation.structure, potential)
                md_calculations.append(md_calculation)

            result = optimize_function(md_calculations, calculations, self.weights)
            parameter_str = ' '.join(['{:12.8g}'.format(_) for _ in parameters])
            optimization_str = '%12.6f %12.6f %12.6f %12.6f' % (result['parts']['forces'], result['parts']['stress'], result['parts']['energy'], result['score'])
            print(parameter_str, '|', optimization_str)
            return result['score']

        result = optimize.minimize(
            fun=optimization_function,
            x0=initial_potential.optimization_parameters,
            method=self.method,
            bounds=initial_potential.optimization_bounds,
            tol=self.step_tolerance,
            options={'disp': True, 'maxiter': self.max_iterations}
        )
        print(result)

    def predict(self, structure):
        pass
