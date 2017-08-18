import numpy as np
from scipy import optimize

from .optimize import evaluate, optimize_function


class Dftfit:
    """ DFT Fitting calculations

    Arguments:


    """

    MD_SOLVERS = {'LAMMPS'}

    def __init__(self,
                 weight_forces=0.8, weight_stress=0.1, weight_energy=0.1,
                 step_jacobian=1e-5, method="L-BFGS-B",
                 max_iterations=100, step_tolerance=1e-6):
        self.max_iterations = max_iterations
        self.step_tolerance = step_tolerance
        self.step_jacobian = step_jacobian
        self.method = method

        if not np.isclose(sum([weight_forces, weight_stress, weight_energy]), 1.0, 1e-8):
            raise ValueError('sum of weighting functions must be one')

        self.weights = {
            'forces': weight_forces,
            'stress': weight_stress,
            'energy': weight_energy
        }

    def _normalize_parameters(self, potential):
        bound_range = potential.optimization_bounds[:, 1] - potential.optimization_bounds[:, 0]
        range_within_limit = (1e-8 < bound_range) & (bound_range < 1e12)
        subtraction_vector = np.where(range_within_limit, potential.optimization_bounds[:, 0], 0)
        scale_vector = np.where(range_within_limit, potential.optimization_bounds[:, 1], 1)
        self._normalized_bounds = np.where(np.column_stack((range_within_limit, range_within_limit)), np.array([0, 1]), potential.optimization_bounds)
        self._normalize_vector = lambda v: (v - subtraction_vector) / scale_vector
        self._unnormalize_vector = lambda v: (v * scale_vector) + subtraction_vector


    def fit(self, calculations, initial_potential):
        """

        Args:
           - calculations: training set of DFT calculations to fit
           - potential: model of Potential to fit
        """
        self._normalize_parameters(initial_potential)
        initial_normalized_parameters = self._normalize_vector(initial_potential.optimization_parameters)

        def optimization_function(parameters):
            potential = initial_potential.copy()
            potential.optimization_parameters = self._unnormalize_vector(parameters)
            md_calculations = []

            for calculation in calculations:
                md_calculation = evaluate('LAMMPS', calculation.structure, potential)
                md_calculations.append(md_calculation)

            result = optimize_function(md_calculations, calculations, self.weights)
            parameter_str = ' '.join(['{:12.8g}'.format(_) for _ in (potential.optimization_parameters)])
            print(parameter_str)
            parameter_str = ' '.join(['{:12.8g}'.format(_) for _ in (potential.optimization_parameters - initial_potential.optimization_parameters)])
            optimization_str = '%12.6f %12.6f %12.6f %12.6f' % (result['parts']['forces'], result['parts']['stress'], result['parts']['energy'], result['score'])
            print(parameter_str, '|', optimization_str)
            return result['score']

        print('It is recommended to bound all parameters for better convergence')
        print('Initial Parameters:')
        print(' '.join(['{:12.8g}'.format(_) for _ in initial_potential.optimization_parameters]))
        result = optimize.minimize(
            fun=optimization_function,
            x0=initial_normalized_parameters,
            method=self.method,
            bounds=self._normalized_bounds,
            jac=False,
            tol=self.step_tolerance,
            options={'disp': True, 'maxiter': self.max_iterations, 'eps': self.step_jacobian}
        )
        print(result)

    def predict(self, structure):
        pass
