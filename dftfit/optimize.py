from itertools import combinations
from tempfile import TemporaryDirectory
import math

import numpy as np

from .io.lammps import LammpsWriter, LammpsRunner


def evaluate(runner, structure, potential):
    if runner == 'LAMMPS':
        with TemporaryDirectory() as tempdir:
            writer = LammpsWriter(structure, potential)
            return LammpsRunner().run(writer, ['lammps', '-i', 'lammps.in'], tempdir)
    else:
        raise ValueError('unknown runner')


def optimize_function(md_calculations, dft_calculations, weights):
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

    score = (
        weights['forces'] * force_sq_error + \
        weights['stress'] * stress_sq_error + \
        weights['energy'] * energy_sq_error
    )

    return {
        'weights': {'forces': weights['forces'], 'stress': weights['stress'], 'energy': weights['energy']},
        'parts': {'forces': force_sq_error, 'stress': stress_sq_error, 'energy': energy_sq_error},
        'score': score
    }


# def optimize():
#     # where to optimize potential based on condition
#     if package == 'scipy':
#         minimize(
#             fun=optimize_function,
#             x0=self.initial_parameters,
#             method="L-BFGS-B",
#             #method="powell",
#             #method="COBYLA",
#             #method="TNC",
#             #method="SLSQP",
#             jac=False,
#             bounds=self.bounds,
#             options={'disp': True},
#         )
#     elif package == 'nlopt':
#         # NLOPT optimization solver
#         # used because reference exists that shows algorithm works
#         # Using BOBYQA algorithm
#         # http://ab-initio.mit.edu/wiki/index.php/NLopt_Algorithms#BOBYQA
#         opt = nlopt.opt(nlopt.LN_BOBYQA, len(self.initial_parameters))
#         lower_bounds, upper_bounds = zip(*self.bounds)

#         self.logger.info((
#             "Using {} optimization algorithm with {} parameters\n"
#             "{}\n"
#         ).format(opt.get_algorithm(), opt.get_dimension(), opt.get_algorithm_name()))

#         opt.set_lower_bounds(lower_bounds)
#         opt.set_upper_bounds(upper_bounds)

#         self.logger.info((
#             "\nBounded Problem:\n"
#             "Lower Bound: {}\n"
#             "Upper Bound: {}\n"
#         ).format(opt.get_lower_bounds(), opt.get_upper_bounds()))

#         opt.set_min_objective(optimize_function)
#         opt.set_ftol_rel(1e-6)
#         # opt.set_maxeval(0) # 0 or negative for no limit
#         # opt.set_maxtime(0) # seconds (0 or negative for no limit)
#         optimized_parameters = opt.optimize(list(self.initial_parameters))
#         min_objective_value = opt.last_optimum_value()
#     else:
#         raise ValueError('Optimzation Packages %s not recognized' % package)
#     pass
