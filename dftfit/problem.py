from itertools import combinations
import math
import asyncio
import logging

import numpy as np

from .db_actions import write_evaluation
from .io.lammps import LammpsLocalDFTFITCalculator
from .io.lammps_cython import LammpsCythonDFTFITCalculator

logger = logging.getLogger(__name__)


class DFTFITProblemBase:
    def __init__(self, potential, dft_calculations, calculator='lammps', dbm=None, run_id=None, loop=None, **kwargs):
        calculator_mapper = {
            'lammps': LammpsLocalDFTFITCalculator,
            'lammps_cython': LammpsCythonDFTFITCalculator,
        }

        self.dft_calculations = dft_calculations
        self.loop = loop or asyncio.get_event_loop()
        structures = [c.structure for c in dft_calculations]
        self.calculator = calculator_mapper[calculator](structures=structures, **kwargs)
        self.loop.run_until_complete(self.calculator.create())
        self.potential = potential

        self.dbm = dbm
        self._run_id = run_id
        if self.dbm and not isinstance(self._run_id, int):
            raise ValueError('cannot write evaluation to database without integer run_id')

    def store_evaluation(self, potential, result):
        if self.dbm:
            write_evaluation(self.dbm, self._run_id, potential, result)

    def __deepcopy__(self, memo):
        return self # override copy method

    def __del__(self):
        self.calculator.shutdown()

    def get_bounds(self):
        return tuple(zip(*self.potential.optimization_bounds.tolist()))


class DFTFITSingleProblem(DFTFITProblemBase):
    def __init__(self, w_f, w_s, w_e, **kwargs):
        super().__init__(**kwargs)
        self.weights = {'forces': w_f, 'stress': w_s, 'energy': w_e}

    def get_nobj(self):
        return 1

    def fitness(self, parameters):
        potential = self.potential.copy()
        potential.optimization_parameters = parameters
        md_calculations = self.loop.run_until_complete(self.calculator.submit(potential))
        result = singleobjective_function(self.dft_calculations, md_calculations, self.weights)
        self.store_evaluation(potential, result)
        logger.info(f'evaluation: {result["score"]}')
        return (result['score'],)


class DFTFITMultiProblem(DFTFITProblemBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_nobj(self):
        return 3

    def fitness(self, parameters):
        potential = self.potential.copy()
        potential.optimization_parameters = parameters
        md_calculations = self.loop.run_until_complete(self.calculator.submit(potential))
        result = multiobjective_function(self.dft_calculations, md_calculations)
        self.store_evaluation(potential, result)
        logger.info(f'evaluation: {result["score"]}')
        return result['score']


def multiobjective_function(md_calculations, dft_calculations):
    n_force_sq_error = 0.0
    d_force_sq_error = 0.0
    n_stress_sq_error = 0.0
    d_stress_sq_error = 0.0
    n_energy_sq_error = 0.0
    d_energy_sq_error = 0.0

    for md_calculation, dft_calculation in zip(md_calculations, dft_calculations):
        n_force_sq_error += np.sum((md_calculation.forces - dft_calculation.forces)**2.0)
        d_force_sq_error += np.sum(dft_calculation.forces**2.0)

        n_stress_sq_error += np.sum((md_calculation.stress - dft_calculation.stress)**2.0)
        d_stress_sq_error += np.sum(dft_calculation.stress**2.0)

    for (md_calc_i, dft_calc_i), (md_calc_j, dft_calc_j) in combinations(zip(md_calculations, dft_calculations), 2):
        n_energy_sq_error += ((md_calc_i.energy - md_calc_j.energy) - (dft_calc_i.energy - dft_calc_j.energy))**2.0
        d_energy_sq_error += (dft_calc_i.energy - dft_calc_j.energy)**2.0

    force_sq_error = math.sqrt(n_force_sq_error / d_force_sq_error)
    stress_sq_error = math.sqrt(n_stress_sq_error / d_stress_sq_error)
    energy_sq_error = math.sqrt(n_energy_sq_error / d_energy_sq_error)

    parts = {'forces': force_sq_error, 'stress': stress_sq_error, 'energy': energy_sq_error}
    score = (force_sq_error, stress_sq_error, energy_sq_error)
    return {'parts': parts, 'score': score}


def singleobjective_function(md_calculations, dft_calculations, weights):
    """ A simple method of scalarizing a multiobjective function:
    https://en.wikipedia.org/wiki/Multi-objective_optimization#Scalarizing

    """
    result = multiobjective_function(md_calculations, dft_calculations)
    result['score'] = (
        weights['forces'] * result['parts']['forces'] + \
        weights['stress'] * result['parts']['stress'] + \
        weights['energy'] * result['parts']['energy']
    )
    result['weights'] = {'forces': weights['forces'], 'stress': weights['stress'], 'energy': weights['energy']}
    return result
