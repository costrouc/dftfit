import copy
import multiprocessing
import time
import logging

from .utils import set_naive_attr_path

logger = logging.getLogger(__name__)


def apply_batch_schema_on_schemas(configuration_schema, potential_schema, training_schema, batch_schema):
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

    logger.info('(batch) %d jobs will be scheduled' % num_jobs)

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

    return full_schemas


def naive_scheduler(full_schemas, scheduler_frequency=5, max_cpus=None):
    """ Naive Scheduler (FIFO) schedules up to max cpus
    uses num_workers field in configuration + 1 (to account for master)
    dask would be a good choice in the future (if can account for jobs that
    take more than more processor).
    """
    from .dftfit import dftfit

    max_cpus = max_cpus or multiprocessing.cpu_count()

    def filter_jobs_to_many_cpus(full_schemas):
        filtered_full_schemas = []
        for i, full_schema in enumerate(full_schemas):
            if full_schema['configuration']['spec'].get('problem', {}).get('num_workers', 0) > max_cpus:
                logger.warning('skipping job %d becuase requsted cpus is larger than allotment' % i+1)
            else:
                filtered_full_schemas.append(full_schema)
        return filtered_full_schemas

    full_schemas = filter_jobs_to_many_cpus(full_schemas)

    running_jobs = []
    current_cpu_used = 0
    result_queue = multiprocessing.Queue()

    def run_dftfit(full_schema, task_id, result_queue):
        run_id = dftfit(
            full_schema['configuration'],
            full_schema['potential'],
            full_schema['training'])
        result_queue.put((task_id, run_id))

    submitted_tasks = 0
    while len(full_schemas) or len(running_jobs):
        if len(full_schemas):
            next_cpus_requested = full_schemas[0]['configuration']['spec'].get('problem', {}).get('num_workers', 1)
            if max_cpus - current_cpu_used >= next_cpus_requested:
                logger.info('(batch) scheduled dftfit task id: %d' % submitted_tasks)
                full_schema = full_schemas.pop(0)
                p = multiprocessing.Process(target=run_dftfit, args=(
                    full_schema, submitted_tasks, result_queue))
                p.start()
                running_jobs.append((p, next_cpus_requested))
                current_cpu_used += next_cpus_requested
                submitted_tasks += 1

        time.sleep(scheduler_frequency)
        completed_jobs = [num_cpus for p, num_cpus in running_jobs if not p.is_alive()]
        running_jobs = [(p, num_cpus) for p, num_cpus in running_jobs if p.is_alive()]

        if completed_jobs:
            logger.info('(batch) %d dftfit jobs just completed' % len(completed_jobs))
        current_cpu_used = current_cpu_used - sum(completed_jobs)

    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    run_ids = [run_id for task_id, run_id in sorted(results, key=lambda r: r[0])]
    logger.info('(batch) run ids of completed jobs: %s' % run_ids)
    return run_ids
