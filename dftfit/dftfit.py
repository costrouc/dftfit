from .potential import Potential
from .training import Training
from .config import Configuration
from .optimize import Optimize

from .db import write_run_initial, write_run_final


def dftfit(configuration_schema, potential_schema, training_schema):
    configuration = Configuration(configuration_schema)
    potential = Potential(potential_schema)
    training = Training(training_schema, **configuration.training_kwargs)

    try:
        potential_hash, run_id = write_run_initial(configuration.dbm, potential, training, configuration)
        optimize = Optimize(
            potential=potential,
            training=training,
            # database
            dbm=configuration.dbm,
            db_write_interval=configuration.db_write_interval,
            # algorithm
            algorithm=configuration.algorithm,
            algorithm_kwargs=configuration.algorithm_kwargs,
            # problem
            features=configuration.features,
            weights=configuration.weights,
            problem_kwargs=configuration.problem_kwargs,
            run_id=run_id
        )

        # if include initial guess replace one random guess with initial
        if configuration.include_initial_guess:
            population_size = configuration.population - 1
        else:
            population_size = configuration.population
        population = optimize.population(configuration.population, seed=configuration.seed)
        if configuration.include_initial_guess:
            population.push_back(potential.optimization_parameters)

        optimize.optimize(population, steps=configuration.steps, seed=configuration.seed)
    except KeyboardInterrupt:
        print(f'\nShutting down DFTFIT\nIf using database all completed evaluations are written')
    finally:
        write_run_final(configuration.dbm, run_id)
    return run_id
