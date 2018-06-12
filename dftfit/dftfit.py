from .potential import Potential
from .training import Training
from .config import Configuration
from .optimize import Optimize

from .db_actions import write_run_initial, write_run_final


def dftfit(configuration_schema, potential_schema, training_schema):
    configuration = Configuration(configuration_schema)
    potential = Potential(potential_schema)
    training = Training(training_schema, **configuration.training_kwargs)

    try:
        potential_id, run_id = write_run_initial(configuration.dbm, potential, training, configuration)
        optimize = Optimize(
            dft_calculations=training.calculations,
            potential=potential,
            dbm=configuration.dbm,
            algorithm=configuration.algorithm,
            algorithm_kwargs=configuration.algorithm_kwargs,
            problem_kwargs=configuration.problem_kwargs,
            run_id=run_id
        )
        population = optimize.population(configuration.population, seed=configuration.seed)
        optimize.optimize(population, steps=configuration.steps, seed=configuration.seed)
    except KeyboardInterrupt:
        print(f'\nShutting down DFTFIT\nIf using database all completed evaluations are written')
    finally:
        write_run_final(configuration.dbm, run_id)
    return run_id
