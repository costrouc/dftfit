import copy
import multiprocessing
import time
import logging

from .utils import set_naive_attr_path
from .config import Configuration
from .db import DatabaseManager

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


def naive_scheduler(full_schemas, scheduler_frequency=5, monitor_interval=60, max_cpus=None):
    """ Naive Scheduler (FIFO) schedules up to max cpus
    uses num_workers field in configuration + 1 (to account for master)
    dask would be a good choice in the future (if can account for jobs that
    take more than more processor).
    """
    from .dftfit import dftfit_process

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
    results_dict = {}
    submitted_tasks = 0

    while len(full_schemas) or len(running_jobs):
        # Schedule a process
        if len(full_schemas):
            next_cpus_requested = full_schemas[0]['configuration']['spec'].get('problem', {}).get('num_workers', 1)
            if max_cpus - current_cpu_used >= next_cpus_requested:
                logger.info('(batch) scheduled dftfit task id: %d' % submitted_tasks)
                full_schema = full_schemas.pop(0)
                p = multiprocessing.Process(target=dftfit_process, args=(
                    full_schema, submitted_tasks, result_queue))
                p.start()
                results_dict[submitted_tasks] = {
                    'process': p,
                    'num_cpus': next_cpus_requested,
                    'run_id': None,
                    'last_id': None,
                    'last_time': None,
                    'dbm': None}
                current_cpu_used += next_cpus_requested
                submitted_tasks += 1

        # Update completed and running jobs
        time.sleep(scheduler_frequency)
        completed_jobs = [v['num_cpus'] for k, v in results_dict.items() if not v['process'].is_alive()]
        running_jobs = [k for k, v in results_dict.items() if v['process'].is_alive()]

        if completed_jobs:
            logger.info('(batch) %d dftfit jobs just completed' % len(completed_jobs))
        current_cpu_used = current_cpu_used - sum(completed_jobs)

        # Check that running taks are making progress
        while not result_queue.empty():
            task_id, database_filename, run_id = result_queue.get()
            results_dict[task_id].update({
                'last_time': time.time(),
                'run_id': run_id,
                'dbm': DatabaseManager(database_filename)})

        for task_id, value in results_dict.items():
            # skipped finished tasks
            if not value['process'].is_alive():
                continue
            run_id = value['run_id']
            last_id = value['last_id'] or 0
            count = value['dbm'].connection.execute('SELECT count(*) FROM evaluation WHERE run_id = ? AND evaluation_id > ?', (run_id, last_id)).fetchone()
            if count > 0:
                value['time_elapsed'] = time.time()
            elif (time.time() - value['last_time']) > monitor_interval:
                logger.warning('(batch) killing process task id %d' % (k))
                value['process'].kill()
                value['process'].wait()
                current_cpu_used -= value['num_cpus']

    run_ids = sorted([v['run_id'] for k, v in results_dict.items()])
    logger.info('(batch) run ids of completed jobs: %s' % run_ids)
    return run_ids
