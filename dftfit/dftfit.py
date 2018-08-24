import copy
import multiprocessing
import time

from .potential import Potential
from .training import Training
from .config import Configuration
from .optimize import Optimize

from .db import write_run_initial, write_run_final
from .utils import set_naive_attr_path


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


def dftfit_batch(configuration_schema, potential_schema, training_schema, batch_schema):
    """ Asisting with batch calculations in dftfit on a single node

    available keys:
      "configuration.<path>"
      "potential.<path>"
      "training.<path>"

    if key value is a list all lists must be the same length
    """

    # Calculate number of jobs
    num_jobs = None
    for key, value in batch_schema.get('spec', {}).get('jobs', {}).items():
        if isinstance(value, list):
            if num_jobs is None:
                num_jobs = len(value)
            elif num_jobs != len(value):
                raise ValueError('All list lengths must be equal for batch job spec')
    if num_jobs is None:
        num_jobs = 1

    # All available schemas
    full_schemas = []
    for i in range(num_jobs):
        full_schema = copy.deepcopy({
            'configuration': configuration_schema,
            'potential': potential_schema,
            'training': training_schema
        })
        for key, value in batch_schema.get('spec', {}).get('jobs', {}).items():
            if isinstance(value, list):
                set_naive_attr_path(full_schema, key, value[i])
            else:
                set_naive_attr_path(full_schema, key, value)
        full_schemas.append(full_schema)

    # Naive Scheduler (FIFO) schedules up to max cpus
    # uses num_workers field in configuration + 1 (to account for master)
    # dask would be a good choice in the future (if can account for jobs that
    # take more than more processor).
    running_jobs = []
    current_cpu_used = 0
    scheduler_frequency = batch_schema.get('spec', {}).get(
        'scheduler_frequency', 5)
    max_cpus = batch_schema.get('spec', {}).get(
        'max_cpus', multiprocessing.cpu_count())
    while len(full_schemas):
        next_cpus_requested = full_schemas[0]['configuration']['spec'].get('problem', {}).get('num_workers', 1) + 1
        if max_cpus - current_cpu_used >= next_cpus_requested:
            full_schema = full_schemas.pop(0)
            p = multiprocessing.Process(target=dftfit, args=(full_schema['configuration'], full_schema['potential'], full_schema['training']))
            p.start()
            running_jobs.append((p, next_cpus_requested))
            current_cpu_used += next_cpus_requested

        time.sleep(scheduler_frequency)
        completed_jobs = [num_cpus for p, num_cpus in running_jobs if not p.is_alive()]
        running_jobs = [(p, num_cpus) for p, num_cpus in running_jobs if p.is_alive()]
        current_cpu_used = current_cpu_used - sum(completed_jobs)

    return num_jobs
