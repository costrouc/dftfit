import json
import hashlib
import datetime as dt
import tempfile
import os
import asyncio

import numpy as np
from scipy import optimize

from .optimize import optimize_function
from .db import DatabaseManager, Base, Potential, Run, Evaluation
from .io import LammpsRunner


class Dftfit:
    """ DFT Fitting calculations

    Arguments:


    """

    MD_BACKENDS = {'LAMMPS'}

    def __init__(self,
                 weight_forces=0.8, weight_stress=0.1, weight_energy=0.1,
                 step_jacobian=1e-5, method="L-BFGS-B", normalize=False,
                 max_iterations=100, step_tolerance=1e-6,
                 cores=1, md_backend='LAMMPS',
                 database_filename=None):
        self.max_iterations = max_iterations
        self.step_tolerance = step_tolerance
        self.step_jacobian = step_jacobian
        self.method = method
        self.normalize = normalize
        self.num_cores = cores
        self.md_backend = md_backend

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

    def _log_initial(self, initial_potential):
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
            self._potential_id = potential.id
            self._run_id = run.id
        print('Initial Parameters:')
        print(' '.join(['{:12.8g}'.format(_) for _ in initial_potential.optimization_parameters]))

    def _log_step(self, current_potential, initial_potential, result, step):
        with self.db.transaction() as session:
            evaluation = Evaluation(
                potential_id=self._potential_id,
                run_id=self._run_id,
                step=step,
                parameters=json.dumps(current_potential.optimization_parameters.tolist()),
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
        parameter_str = ' '.join(['{:12.8g}'.format(_) for _ in (current_potential.optimization_parameters - initial_potential.optimization_parameters)])
        optimization_str = '%12.6f %12.6f %12.6f %12.6f' % (result['parts']['forces'], result['parts']['stress'], result['parts']['energy'], result['score'])
        print(parameter_str, '|', optimization_str)

    def _log_final(self, result):
        print(result)
        with self.db.transaction() as session:
            run = session.query(Run).filter(Run.id == self._run_id).one()
            run.end_time = dt.datetime.utcnow()
            session.add(run)

    def fit(self, calculations, initial_potential):
        """

        Args:
           - calculations: training set of DFT calculations to fit
           - potential: model of Potential to fit
        """
        runner_map = {
            'LAMMPS': LammpsRunner
        }

        self._loop = asyncio.get_event_loop()
        self._normalize_parameters(initial_potential)
        self._log_initial(initial_potential)

        runner = runner_map[self.md_backend](calculations, max_workers=self.num_cores, cmd=['lammps'])
        self._loop.run_until_complete(runner.initialize())

        step = 0
        def optimization_function(parameters):
            nonlocal step
            potential = initial_potential.copy()
            potential.optimization_parameters = self._unnormalize_vector(parameters)
            md_calculations = self._loop.run_until_complete(runner.calculate(potential))
            result = optimize_function(md_calculations, calculations, self.weights)
            self._log_step(potential, initial_potential, result, step)
            step += 1
            return result['score']

        result = optimize.minimize(
            fun=optimization_function,
            x0=self._normalize_vector(initial_potential.optimization_parameters),
            method=self.method,
            bounds=self._normalized_bounds,
            jac=False,
            tol=self.step_tolerance,
            options={'disp': True, 'maxiter': self.max_iterations, 'eps': self.step_jacobian}
        )
        self._log_final(result)
        self._loop.run_until_complete(runner.finalize())
        return result

    def predict(self, structure):
        pass
