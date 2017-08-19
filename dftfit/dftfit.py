import json
import hashlib
import datetime as dt

import numpy as np
from scipy import optimize

from .optimize import evaluate, optimize_function
from .db import DatabaseManager, Base, Potential, Run, Evaluation


class Dftfit:
    """ DFT Fitting calculations

    Arguments:


    """

    MD_SOLVERS = {'LAMMPS'}

    def __init__(self,
                 weight_forces=0.8, weight_stress=0.1, weight_energy=0.1,
                 step_jacobian=1e-5, method="L-BFGS-B", normalize=False,
                 max_iterations=100, step_tolerance=1e-6,
                 database_filename=None):
        self.max_iterations = max_iterations
        self.step_tolerance = step_tolerance
        self.step_jacobian = step_jacobian
        self.method = method
        self.normalize = normalize

        if not np.isclose(sum([weight_forces, weight_stress, weight_energy]), 1.0, 1e-8):
            raise ValueError('sum of weighting functions must be one')

        self.db = DatabaseManager('dftfit.db')
        self.db.create_tables(Base)

        self.weights = {
            'forces': weight_forces,
            'stress': weight_stress,
            'energy': weight_energy
        }

    def _normalize_parameters(self, potential):
        if self.normalize:
            bound_range = potential.optimization_bounds[:, 1] - potential.optimization_bounds[:, 0]
            range_within_limit = (1e-8 < bound_range) & (bound_range < 1e12)
            subtraction_vector = np.where(range_within_limit, potential.optimization_bounds[:, 0], 0)
            scale_vector = np.where(range_within_limit, bound_range, 1)
            self._normalized_bounds = np.where(np.column_stack((range_within_limit, range_within_limit)), np.array([0, 1]), potential.optimization_bounds)
            self._normalize_vector = lambda v: (v - subtraction_vector) / scale_vector
            self._unnormalize_vector = lambda v: (v * scale_vector) + subtraction_vector
        else:
            self._normalize_vector = lambda v: v
            self._unnormalize_vector = lambda v: v
            self._normalized_bounds = potential.optimization_bounds

    def fit(self, calculations, initial_potential):
        """

        Args:
           - calculations: training set of DFT calculations to fit
           - potential: model of Potential to fit
        """
        self._normalize_parameters(initial_potential)

        # Create Potential and Run
        with self.db.transaction() as session:
            potential_str = json.dumps(initial_potential.as_dict(with_parameters=False), sort_keys=True)
            potential_hash = hashlib.md5(potential_str.encode('utf-8')).hexdigest()
            potential = session.query(Potential).filter(Potential.id == potential_hash).one_or_none()
            if potential is None:
                potential = Potential(id=potential_hash, schema=potential_str)
                session.add(potential)

            run = Run(
                potential_id=potential.id,
                start_time=dt.datetime.utcnow(),
                initial_parameters=json.dumps(initial_potential.parameters.tolist()),
                indicies=json.dumps(initial_potential.optimization_parameter_indicies.tolist()),
                bounds=json.dumps(initial_potential.optimization_bounds.tolist())
            )
            session.add(run)
            session.flush()
            potential_id = potential.id
            run_id = run.id

        step = 0
        def optimization_function(parameters):
            nonlocal step
            potential = initial_potential.copy()
            potential.optimization_parameters = self._unnormalize_vector(parameters)
            md_calculations = []

            for calculation in calculations:
                md_calculation = evaluate('LAMMPS', calculation.structure, potential)
                md_calculations.append(md_calculation)

            result = optimize_function(md_calculations, calculations, self.weights)

            with self.db.transaction() as session:
                evaluation = Evaluation(
                    potential_id=potential_id,
                    run_id=run_id,
                    step=step,
                    sq_force_error=result['parts']['forces'],
                    sq_stress_error=result['parts']['stress'],
                    sq_energy_error=result['parts']['energy'],
                    weight_forces=result['weights']['forces'],
                    weight_stress=result['weights']['stress'],
                    weight_energy=result['weights']['energy'],
                    score=result['score']
                )
                session.add(evaluation)

            # Create Evaluation of potential in run step
            parameter_str = ' '.join(['{:12.8g}'.format(_) for _ in (potential.optimization_parameters - initial_potential.optimization_parameters)])
            optimization_str = '%12.6f %12.6f %12.6f %12.6f' % (result['parts']['forces'], result['parts']['stress'], result['parts']['energy'], result['score'])
            print(parameter_str, '|', optimization_str)
            step += 1
            return result['score']

        print('It is recommended to bound all parameters for better convergence')
        print('Initial Parameters:')
        print(' '.join(['{:12.8g}'.format(_) for _ in initial_potential.optimization_parameters]))
        result = optimize.minimize(
            fun=optimization_function,
            x0=self._normalize_vector(initial_potential.optimization_parameters),
            method=self.method,
            bounds=self._normalized_bounds,
            jac=False,
            tol=self.step_tolerance,
            options={'disp': True, 'maxiter': self.max_iterations, 'eps': self.step_jacobian}
        )
        print(result)

        with self.db.transaction() as session:
            run = session.query(Run).filter(id=run_id).one()
            run.end_time = dt.datetime.utcnow()

    def predict(self, structure):
        pass
