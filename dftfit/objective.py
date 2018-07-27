"""Defines objective functions used in DFTFIT

"""
import math
import itertools

import numpy as np


def force_objective_function(md_calculations, dft_calculations):
    n_force_sq_error = 0.0
    d_force_sq_error = 0.0
    for md_calculation, dft_calculation in zip(md_calculations, dft_calculations):
        n_force_sq_error += np.sum((md_calculation.forces - dft_calculation.forces)**2.0)
        d_force_sq_error += np.sum(dft_calculation.forces**2.0)
    return math.sqrt(n_force_sq_error / d_force_sq_error)


def stress_objective_function(md_calculations, dft_calculations):
    n_stress_sq_error = 0.0
    d_stress_sq_error = 0.0
    for md_calculation, dft_calculation in zip(md_calculations, dft_calculations):
        n_stress_sq_error += np.sum((md_calculation.stress - dft_calculation.stress)**2.0)
        d_stress_sq_error += np.sum(dft_calculation.stress**2.0)
    return math.sqrt(n_stress_sq_error / d_stress_sq_error)


def energy_objective_function(md_calculations, dft_calculations):
    n_energy_sq_error = 0.0
    d_energy_sq_error = 0.0

    # cannot calculate energy error if only one set of calculations
    if len(md_calculations) == 1:
        return 0.0

    for (md_calc_i, dft_calc_i), (md_calc_j, dft_calc_j) in itertools.combinations(zip(md_calculations, dft_calculations), 2):
        n_energy_sq_error += ((md_calc_i.energy - md_calc_j.energy) - (dft_calc_i.energy - dft_calc_j.energy))**2.0
        d_energy_sq_error += (dft_calc_i.energy - dft_calc_j.energy)**2.0
    return math.sqrt(n_energy_sq_error / d_energy_sq_error)
