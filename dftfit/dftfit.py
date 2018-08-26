import logging

from .potential import Potential
from .training import Training
from .config import Configuration
from .optimize import Optimize
from .batch import apply_batch_schema_on_schemas, naive_scheduler

from .db import write_run_initial, write_run_final

logger = logging.getLogger(__name__)


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
        logger.info('(population) initializing with %d guesses' % configuration.population)
        if configuration.include_initial_guess:
            population_size = configuration.population - 1
        else:
            population_size = configuration.population
        population = optimize.population(configuration.population, seed=configuration.seed)
        if configuration.include_initial_guess:
            logger.info('(population) including initial potential guess')
            population.push_back(potential.optimization_parameters)

        optimize.optimize(population, steps=configuration.steps, seed=configuration.seed)
    except KeyboardInterrupt:
        print(f'\nShutting down DFTFIT\nIf using database all completed evaluations are written')
    finally:
        write_run_final(configuration.dbm, run_id)
    return run_id


def dftfit_batch(configuration_schema, potential_schema, training_schema, batch_schema):
    """ Asisting with batch calculations in dftfit on a single node

    available keys:
      "configuration.<path>"
      "potential.<path>"
      "training.<path>"

    if key value is a list all lists must be the same length
    """
    configuration = Configuration(configuration_schema)
    full_schemas = apply_batch_schema_on_schemas(
        configuration_schema,
        potential_schema,
        training_schema,
        batch_schema)
    return naive_scheduler(full_schemas)
