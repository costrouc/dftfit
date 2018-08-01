import asyncio
import logging

from .db import write_evaluations_batch
from .io.lammps import LammpsLocalDFTFITCalculator
from .io.lammps_cython import LammpsCythonDFTFITCalculator
from . import objective

logger = logging.getLogger(__name__)


class DFTFITProblemBase:
    def __init__(self, potential, training, features, weights, calculator='lammps_cython', dbm=None, db_write_interval=10, run_id=None, loop=None, **kwargs):
        # Calculator Initialization
        dftfit_calculator_mapper = {
            'lammps': LammpsLocalDFTFITCalculator,
            'lammps_cython': LammpsCythonDFTFITCalculator,
        }
        self.loop = loop or asyncio.get_event_loop()

        self.dft_calculations = training.calculations
        self.calculator = dftfit_calculator_mapper[calculator](structures=[c.structure for c in self.dft_calculations], potential=potential, **kwargs)
        self.loop.run_until_complete(self.calculator.create())

        # Potential Initialization
        self.potential = potential



        # Objective Initialization
        self.features = features
        self.weights = weights
        self.objective_functions = []
        for feature in self.features:
            if feature == 'forces':
                self.objective_functions.append(objective.force_objective_function)
            elif feature == 'stress':
                self.objective_functions.append(objective.stress_objective_function)
            elif feature == 'energy':
                self.objective_functions.append(objective.energy_objective_function)

        # Database Logging Initialization
        self.dbm = dbm
        self._run_id = run_id
        self.db_write_interval = db_write_interval
        self._evaluation_buffer = []
        if self.dbm and not isinstance(self._run_id, int):
            raise ValueError('cannot write evaluation to database without integer run_id')

    def store_evaluation(self, potential, errors, value):
        if self.dbm:
            self._evaluation_buffer.append([potential, errors, value])
            if len(self._evaluation_buffer) >= self.db_write_interval:
                write_evaluations_batch(self.dbm, self._run_id, self._evaluation_buffer)
                self._evaluation_buffer = []

    def _fitness(self, parameters):
        potential = self.potential.copy()
        potential.optimization_parameters = parameters
        md_calculations = self.loop.run_until_complete(self.calculator.submit(potential))

        value = 0.0
        errors = []
        for feature, weight, func in zip(self.features, self.weights, self.objective_functions):
            v = func(md_calculations, self.dft_calculations)
            if weight:
                value += v * weight
            errors.append(v)

        self.store_evaluation(potential, errors, value)
        logger.info(f'evaluation: {value}')
        return errors, value

    def __deepcopy__(self, memo):
        return self # override copy method

    def finalize(self):
        if self._evaluation_buffer: # ensure that all evaluations have been written
            write_evaluations_batch(self.dbm, self._run_id, self._evaluation_buffer)
            self._evaluation_buffer = []

    def __del__(self):
        self.calculator.shutdown()

    def get_bounds(self):
        return tuple(zip(*self.potential.optimization_bounds.tolist()))


class DFTFITSingleProblem(DFTFITProblemBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_nobj(self):
        return 1

    def fitness(self, parameters):
        errors, value = self._fitness(parameters)
        return (value,)


class DFTFITMultiProblem(DFTFITProblemBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_nobj(self):
        return len(self.features)

    def fitness(self, parameters):
        errors, value = self._fitness(parameters)
        return tuple(errors)
