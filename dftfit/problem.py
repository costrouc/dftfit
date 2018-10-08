import asyncio
import logging
import time

from .db import write_evaluations_batch
from .io.lammps import LammpsLocalDFTFITCalculator
from .io.lammps_cython import LammpsCythonDFTFITCalculator
from .predict import Predict
from . import objective

logger = logging.getLogger(__name__)


class DFTFITProblemBase:
    def __init__(self, potential, training, features, weights, calculator='lammps_cython', dbm=None, db_write_interval=10, run_id=None, loop=None, **kwargs):
        self.loop = loop or asyncio.get_event_loop()

        # Training Initialization
        self.training = training

        # DFTFIT Calculator Initialization
        dftfit_calculator_mapper = {
            'lammps': LammpsLocalDFTFITCalculator,
            'lammps_cython': LammpsCythonDFTFITCalculator,
        }
        structures = [c.structure for c in self.training.calculations]
        self.dftfit_calculator = dftfit_calculator_mapper[calculator](structures=structures, potential=potential, **kwargs)
        self.loop.run_until_complete(self.dftfit_calculator.create())
        logger.info('(problem) initialized dftfit calculator %s' % calculator)

        # MD Calculator Initialization
        self.md_calculator = None
        if training.material_properties:
            self.md_calculator = Predict(calculator, loop=self.loop)
            logger.info('(problem) initialized md calculator %s' % calculator)

        # Potential Initialization
        self.potential = potential
        logger.info('(problem) potential has %d parameters' % len(potential.optimization_parameters))

        # Objective Initialization
        self.features = features
        self.weights = weights
        self.objective_functions = []
        self.md_calculations = set()
        feature_function_mapping = {
            'forces': objective.force_objective_function,
            'stress': objective.stress_objective_function,
            'energy': objective.energy_objective_function,
            'lattice_constants': objective.lattice_constant_objective_function,
            'elastic_constants': objective.elastic_constants_objective_function,
            'bulk_modulus': objective.bulk_modulus_objective_function,
            'shear_modulus': objective.shear_modulus_objective_function
        }
        for feature in self.features:
            self.objective_functions.append(feature_function_mapping[feature])
            if feature in {'lattice_constants'}:
                self.md_calculations.add('lattice_constants')
            elif feature in {'elastic_constants', 'bulk_modulus', 'shear_modulus'}:
                self.md_calculations = self.md_calculations | {'lattice_constants', 'elastic_constants'}
        logger.info('(problem) optimizing features with weights: ' + ', '.join('{}={:.2f}'.format(f, w) for f, w in zip(self.features, self.weights)))

        # Database Logging Initialization
        self.dbm = dbm
        self._run_id = run_id
        self.db_write_interval = db_write_interval
        self._evaluation_buffer = []
        if self.dbm and not isinstance(self._run_id, int):
            raise ValueError('cannot write evaluation to database without integer run_id')

        # Timing
        self.start_time = time.time()

    def store_evaluation(self, potential, errors, value):
        if self.dbm:
            self._evaluation_buffer.append([potential, errors, value])
            if len(self._evaluation_buffer) >= self.db_write_interval:
                total_time = time.time() - self.start_time
                logger.info('md evaluations per second: %f' % ((len(self._evaluation_buffer) * len(self.training.calculations)) / total_time))
                self.start_time = time.time()
                write_evaluations_batch(self.dbm, self._run_id, self._evaluation_buffer)
                self._evaluation_buffer = []

    def _fitness(self, parameters):
        potential = self.potential.copy()
        potential.optimization_parameters = parameters

        # dftfit calculations
        md_calculations = self.loop.run_until_complete(self.dftfit_calculator.submit(potential))

        # material property calculations
        predict_calculations = {}
        if self.md_calculations:
            if 'lattice_constants' in self.md_calculations:
                old_lattice, new_lattice = self.md_calculator.lattice_constant(self.training.reference_ground_state, potential)
                predict_calculations['lattice_constants'] = new_lattice
            if 'elastic_constants' in self.md_calculations:
                structure = self.training.reference_ground_state.copy()
                structure.modify_lattice(predict_calculations['lattice_constants'])
                predict_calculations['elastic_constants'] = self.md_calculator.elastic_constant(structure, potential)

        value = 0.0
        errors = []
        for feature, weight, func in zip(self.features, self.weights, self.objective_functions):
            if feature in {'forces', 'stress', 'energy'}:
                v = func(md_calculations, self.training.calculations)
            elif feature in {'lattice_constants'}:
                v = func(predict_calculations['lattice_constants'], self.training.material_properties[feature])
            elif feature in {'elastic_constants', 'bulk_modulus', 'shear_modulus'}:
                v = func(predict_calculations['elastic_constants'], self.training.material_properties[feature])

            if weight:
                value += v * weight
            errors.append(v)

        self.store_evaluation(potential, errors, value)
        formatted_errors = ', '.join('{:10.4g}'.format(_) for _ in errors)
        logger.debug(f'evaluation = {value:10.4g} errors = [ {formatted_errors} ]')
        return errors, value

    def __deepcopy__(self, memo):
        return self # override copy method

    def finalize(self):
        if self._evaluation_buffer: # ensure that all evaluations have been written
            write_evaluations_batch(self.dbm, self._run_id, self._evaluation_buffer)
            self._evaluation_buffer = []

    def __del__(self):
        self.dftfit_calculator.shutdown()

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
