import pygmo

from .problem import DFTFITSingleProblem, DFTFITMultiProblem


available_algorithms = {
    'pygmo.de': (pygmo.de, 'S'), # S-U
    'pygmo.sade': (pygmo.sade, 'S'), # S-U
    'pygmo.de1220': (pygmo.pso, 'S'), # S-U
    'pygmo.sea': (pygmo.sea, 'S'), # S-U
    'pygmo.sga': (pygmo.sga, 'S'), # S-U
    # 'pygmo.simulated_annealing': simulated_annealing # api does not match others
    'pygmo.bee_colony': (pygmo.bee_colony, 'S'), # S-U
    'pygmo.cmaes': (pygmo.cmaes, 'S'), # S-U
    'pygmo.nsga2': (pygmo.nsga2, 'M'), # M-U
    'pygmo.moead': (pygmo.moead, 'M') # M-U
}


class Optimize:
    def __init__(self, dft_calculations, potential, algorithm='pygmo.de', algorithm_kwargs=None, problem_kwargs=None, dbm=None):
        self.dbm = dbm
        self.algorithm_name = algorithm
        if self.algorithm_name not in available_algorithms:
            raise ValueError(f'algorithm {self.algorithm_name} not available')
        if available_algorithms[self.algorithm_name][1] == 'S':
            internal_problem = DFTFITSingleProblem(potential=potential, dft_calculations=dft_calculations, dbm=dbm, **problem_kwargs)
        else:
            internal_problem = DFTFITMultiProblem(potential=potential, dft_calculations=dft_calculations, dbm=dbm, **problem_kwargs)
        self._internal_problem = internal_problem
        self._problem = pygmo.problem(internal_problem)
        self.algorithm_kwargs = algorithm_kwargs or {}

    def population(self, size, seed=None):
        return pygmo.population(self._problem, size, seed=seed)

    def optimize(self, population, steps, seed=None, run_id=None):
        algorithm_constructor = available_algorithms[self.algorithm_name][0]
        self._algorithm = pygmo.algorithm(algorithm_constructor(gen=steps, seed=seed, **self.algorithm_kwargs))
        try:
            self._internal_problem.dbm_initialize_run()
            new_population = self._algorithm.evolve(population)
        finally:
            self._internal_problem.dbm_finalize_run()
        return new_population
