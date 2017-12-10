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


class DFTFITOptimize:
    def __init__(self, dft_calculations, potential, algorithm='pygmo.de', algorithm_kwargs=None, problem_kwargs=None):
        self.algorithm_name = algorithm
        if self.algorithm_name not in available_algorithms:
            raise ValueError(f'algorithm {self.algorithm_name} not available')
        if available_algorithms[self.algorithm_name][1] == 'S':
            problem = DFTFITSingleProblem(potential=potential, dft_calculations=dft_calculations, **problem_kwargs)
        else:
            problem = DFTFITMultiProblem(potential=potential, dft_calculations=dft_calculations, **problem_kwargs)
        self._problem = pygmo.problem(problem)
        self.algorithm_kwargs = algorithm_kwargs or {}

    def population(self, size, seed=None):
        return pygmo.population(self._problem, size, seed=seed)

    def optimize(self, population, steps, seed=None):
        algorithm_constructor = available_algorithms[self.algorithm_name][0]
        self._algorithm = pygmo.algorithm(algorithm_constructor(gen=steps, seed=seed, **self.algorithm_kwargs))
        return self._algorithm.evolve(population)
