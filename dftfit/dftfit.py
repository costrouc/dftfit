from .potential import Potential
from .training import Training
from .config import Configuration
from .optimize import Optimize


def dftfit(configuration_schema, potential_schema, training_schema):
    configuration = Configuration(configuration_schema)
    potential = Potential(potential_schema)
    training = Training(training_schema, **configuration.training_kwargs)
    optimize = Optimize(
        dft_calculations=training.calculations,
        potential=potential,
        dbm=configuration.dbm,
        algorithm=configuration.algorithm,
        algorithm_kwargs=configuration.algorithm_kwargs,
        problem_kwargs=configuration.problem_kwargs,
    )
    population = optimize.population(configuration.population, seed=configuration.seed)
    optimize.optimize(population, steps=configuration.steps, seed=configuration.seed)
