from .potential import Potential
from .training import Training
from .config import Configuration
from .optimize import Optimize

from .db_actions import write_run_initial, write_run_final


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

    try:
        potential_id, run_id = write_run_initial(configuration.dbm, potential, configuration)
        optimize.optimize(population, steps=configuration.steps, seed=configuration.seed, run_id=run_id)
    finally:
        write_run_final(configuration.dbm, run_id)
