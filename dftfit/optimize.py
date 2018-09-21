import functools
import logging

import pygmo

from .problem import DFTFITSingleProblem, DFTFITMultiProblem

logger = logging.getLogger(__name__)


available_algorithms = {
    'pygmo.de': (pygmo.de, 'S'),                                            # S-U
    'pygmo.sade': (pygmo.sade, 'S'),                                        # S-U
    'pygmo.de1220': (pygmo.de1220, 'S'),                                    # S-U
    'pygmo.pso': (pygmo.pso, 'S'),                                          # S-U
    'pygmo.sea': (pygmo.sea, 'S'),                                          # S-U
    'pygmo.sga': (pygmo.sga, 'S'),                                          # S-U
    # 'pygmo.simulated_annealing': simulated_annealing # api does not match others
    'pygmo.bee_colony': (pygmo.bee_colony, 'S'),                            # S-U
    # population > 5 and % 4 and most likely will need to set force_bounds=True
    'pygmo.cmaes': (pygmo.cmaes, 'S'),                                      # S-U
    'pygmo.xnes': (pygmo.xnes, 'S'),                                        # S-U
    'pygmo.nsga2': (pygmo.nsga2, 'M'),                                      # M-U
    'pygmo.moead': (pygmo.moead, 'M'),                                      # M-U
    'nlopt.cobyla': (functools.partial(pygmo.nlopt, solver='cobyla'), 'S'), # S-U
    'nlopt.bobyqa': (functools.partial(pygmo.nlopt, solver='bobyqa'), 'S'), # S-U
    'nlopt.newuoa': (functools.partial(pygmo.nlopt, solver='newuoa'), 'S'), # S-U
    'nlopt.sbplx': (functools.partial(pygmo.nlopt, solver='sbplx'), 'S'),   # S-U
}


class Optimize:
    def __init__(self, potential, training,
                 dbm=None, db_write_interval=10,                      # database
                 algorithm='pygmo.de', algorithm_kwargs=None,         # algorithm
                 features=None, weights=None, problem_kwargs=None,    # problem
                 run_id=None):

        self.algorithm_name = algorithm
        if self.algorithm_name not in available_algorithms:
            raise ValueError(f'algorithm {self.algorithm_name} not available')

        _problem_kwargs = {
            'potential': potential,
            'training': training,
            'dbm': dbm, 'db_write_interval': db_write_interval,
            'features': features, 'weights': weights,
            'run_id': run_id,
            **problem_kwargs
        }
        if available_algorithms[self.algorithm_name][1] == 'S':
            internal_problem = DFTFITSingleProblem(**_problem_kwargs)
        else:
            internal_problem = DFTFITMultiProblem(**_problem_kwargs)
        self._internal_problem = internal_problem
        self._problem = pygmo.problem(internal_problem)
        self.algorithm_kwargs = algorithm_kwargs or {}

    def population(self, size, seed=None):
        return pygmo.population(self._problem, size, seed=seed)

    def optimize(self, population, steps, seed=None):
        algorithm_constructor = available_algorithms[self.algorithm_name][0]
        if 'nlopt' in self.algorithm_name: # nlopt algorithms called differently.
            _algorithm = algorithm_constructor()
            _algorithm.maxeval = steps
            self._algorithm = pygmo.algorithm(_algorithm)
        else:
            self._algorithm = pygmo.algorithm(algorithm_constructor(gen=steps, seed=seed, **self.algorithm_kwargs))
        logger.info('(algorithm) using %s algorithm with steps: %d seed: %d' % (self.algorithm_name, steps, seed))

        results = self._algorithm.evolve(population)
        self._internal_problem.finalize()
        return results
