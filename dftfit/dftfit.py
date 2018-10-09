import logging
import os

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
        _dftfit_internal(configuration, potential, training, run_id)
    except KeyboardInterrupt:
        print(f'\nShutting down DFTFIT\nIf using database all completed evaluations are written')
    finally:
        write_run_final(configuration.dbm, run_id)
    return run_id


def dftfit_process(full_schema, task_id, result_queue):
    configuration = Configuration(full_schema['configuration'])
    potential = Potential(full_schema['potential'])
    training = Training(full_schema['training'], **configuration.training_kwargs)

    potential_hash, run_id = write_run_initial(configuration.dbm, potential, training, configuration)
    _dftfit_internal(configuration, potential, training, run_id)
    database_filename = os.path.expanduser(configuration.schema['spec']['database']['filename'])
    result_queue.put((task_id, database_filename, run_id))


def _dftfit_internal(configuration, potential, training, run_id):
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
    scheduler_frequency = batch_schema.get('scheduler_frequency', 5)
    monitor_interval = batch_schema.get('monitor_interval', 60)
    return naive_scheduler(full_schemas, scheduler_frequency, monitor_interval)
