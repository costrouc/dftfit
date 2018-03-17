import json
import hashlib
import datetime as dt
import numpy as np
import pandas as pd

from .potential import Potential


def _write_potential(dbm, potential):
    potential_str = json.dumps(potential.as_dict(with_parameters=False), sort_keys=True)
    potential_hash = hashlib.md5(potential_str.encode('utf-8')).hexdigest()

    result = dbm.connection.execute(
        'SELECT id FROM potential WHERE potential.hash = ?',
        (potential_hash,)).fetchone()
    if result:
        return result['id']

    cursor = dbm.connection.execute(
        'INSERT INTO potential (hash, schema) VALUES (?, ?)',
        (potential_hash, potential.as_dict(with_parameters=False))
    )
    return cursor.lastrowid


def _write_training(dbm, training):
    training_str = json.dumps(training.schema, sort_keys=True)
    training_hash = hashlib.md5(training_str.encode('utf-8')).hexdigest()

    result = dbm.connection.execute(
        'SELECT id FROM training WHERE training.hash = ?',
        (training_hash,)).fetchone()
    if result:
        return result['id']

    cursor = dbm.connection.execute(
        'INSERT INTO training (hash, schema) VALUES (?, ?)',
        (training_hash, training.schema)
    )
    return cursor.lastrowid


def _write_labels(dbm, run_id, labels):
    for key, value in labels.items():
        result = dbm.connection.execute('''
        SELECT id FROM label
        WHERE label.key = ? AND label.value = ?
        ''', (key, value)).fetchone()

        if result:
            label_id = result['id']
        else:
            cursor = dbm.connection.execute('''
            INSERT INTO label (key, value)
            VALUES (?, ?)
            ''', (key, value))
            label_id = cursor.lastrowid

        cursor = dbm.connection.execute('''
        INSERT INTO run_label (run_id, label_id)
        VALUES (?, ?)
        ''', (run_id, label_id))


def write_run_initial(dbm, potential, training, configuration):
    with dbm.connection:
        potential_id = _write_potential(dbm, potential)
        training_id = _write_training(dbm, training)
        cursor = dbm.connection.execute('''
        INSERT INTO run (name, potential_id, training_id, configuration, start_time, initial_parameters, indicies, bounds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            configuration.run_name,
            potential_id,
            training_id,
            configuration.schema,
            dt.datetime.utcnow(),
            potential.parameters.tolist(),
            potential.optimization_parameter_indicies.tolist(),
            potential.optimization_bounds.tolist()
        ))
        run_id = cursor.lastrowid
        _write_labels(dbm, run_id, configuration.run_labels)
        return potential_id, run_id


def write_run_final(dbm, run_id):
    with dbm.connection:
        cursor = dbm.connection.execute('''
        UPDATE run SET end_time = ?
        WHERE id = ? AND end_time IS NULL
        ''', (dt.datetime.utcnow(), run_id))


def write_evaluation(dbm, run_id, potential, result):
    with dbm.connection:
        errors = (
            result['parts']['forces'],
            result['parts']['stress'],
            result['parts']['energy'])
        if 'weights' in result:
            weights = (
                result['weights']['forces'],
                result['weights']['stress'],
                result['weights']['energy']
            )
        else:
            weights = (0, 0, 0)
        cursor = dbm.connection.execute('''
        INSERT INTO evaluation (run_id, parameters, sq_force_error, sq_stress_error, sq_energy_error, w_f, w_s, w_e)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (run_id, potential.optimization_parameters.tolist(),
              *errors, *weights))


def filter_evaluations(dbm, potential=None, limit=10, condition='best', run_id=None, labels=None):
    """Select a subset of evaluations. Currently only works on single
    objective functions because "best" and "worst" are subjective in
    multiobjecive functions.

    Arguments:
     - condition (str): best, random, worst

    THIS IS THE REASON TO USE SQLALCHEMY QUERY BUILDER.... I HAVE LEARNED NOW
    """

    query = '''
    SELECT run.id
    FROM run {join_sql}
    WHERE {where_sql}
    '''

    join_statement = []
    where_statement = ['1=1']
    query_arguments = []
    if labels:
        join_statement.extend([
            'JOIN run_label ON run.id = run_label.run_id',
            'JOIN label ON run_label.label_id = label.id'
        ])
        select_labels = []
        for key, value in labels.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(f'key: {key} values: {values} for label must be strings')
            select_labels.append('(label.key = ? AND label.value = ?)')
            query_arguments.extend([key, value])
        where_statement.append(' OR '.join(select_labels))
        query += f"""
        GROUP BY run.id
        HAVING count = {len(labels)}
        """

    if run_id is not None:
        if not isinstance(run_id, int):
            raise ValueError('run_id must be integer')
        where_statement.append('run.id = ?')
        query_arguments.append(run_id)

    if potential:
        potential_str = json.dumps(potential.as_dict(with_parameters=False), sort_keys=True)
        potential_hash = hashlib.md5(potential_str.encode('utf-8')).hexdigest()
        join_statement.append('JOIN potential ON run.potential_id = potential.id')
        where_statement.append('potential.hash = ?')
        query_arguments.append(potential_hash)

    # find all run ids that match selection
    query = query.format(join_sql=' '.join(join_statement),
                         where_sql=' AND '.join(where_statement))
    run_ids = [row['id'] for row in dbm.connection.execute(query, query_arguments)]

    if condition == 'best':
        order_sql = 'score ASC'
    elif condition == 'worst':
        order_sql = 'score DESC'
    elif condition == 'random':
        order_sql = 'RANDOM()'
    else:
        raise ValueError('condition ordering not supported')

    # pick subset of potentials
    query = f'''
    SELECT e.id, e.parameters, (e.w_f * e.sq_force_error + e.w_s * e.sq_stress_error + e.w_e * e.sq_energy_error) AS score FROM evaluation e
    WHERE {' OR '.join(['e.run_id = ?' for _ in run_ids])}
    ORDER BY {order_sql}
    LIMIT {limit}
    '''
    return dbm.connection.execute(query, run_ids)


def filter_potentials(dbm, potential=None, limit=10, condition='best', run_id=None, labels=None):
    results = []
    for row in filter_evaluations(dbm, potential, limit, condition, run_id, labels):
        results.append({'potential': select_potential_from_evaluation(dbm, row['id']), 'score': row['score']})
    return results


def select_potential_from_evaluation(dbm, evaluation_id):
    result = dbm.connection.execute('''
    SELECT potential.schema, parameters, initial_parameters, indicies, bounds
    FROM evaluation
        JOIN run ON run.id = evaluation.run_id
        JOIN potential ON potential.id = run.potential_id
    WHERE evaluation.id = ?
    ''', (evaluation_id,)).fetchone()
    if result is None:
        raise ValueError(f'evaluation_id {evaluation_id} does not exist')

    return Potential.from_run_evaluation(
        result['schema'],
        result['initial_parameters'],
        result['indicies'], result['parameters'], result['bounds'])


def copy_database_to_database(src_dbm, dest_dbm, only_unique=False):
    SELECT_RUNS = 'SELECT id FROM run'
    SELECT_RUN = 'SELECT id, name, potential_id, training_id, configuration, start_time, end_time, initial_parameters, indicies, bounds FROM run WHERE id = ?'
    SELECT_RUN_LABELS = 'SELECT label.key, label.value FROM run_label JOIN label ON run_label.label_id = label.id WHERE run_label.run_id = ?'
    SELECT_RUN_POTENTIAL = 'SELECT potential.hash, potential.schema FROM potential JOIN run ON run.potential_id = potential.id WHERE run.id = ?'
    SELECT_RUN_TRAINING = 'SELECT training.hash, training.schema FROM training JOIN run ON run.potential_id = training.id WHERE run.id = ?'
    SELECT_RUN_EVALUATION_COUNT = 'SELECT count(*) as num_evaluations FROM evaluation WHERE run_id = ?'
    SELECT_RUN_EVALUATION = '''
    SELECT parameters, sq_force_error, sq_stress_error, sq_energy_error, w_f, w_s, w_e FROM evaluation
    WHERE run_id = ? ORDER BY id LIMIT ? OFFSET ?
    '''

    UNIQUE_RUN_POTENTIAL = 'SELECT id, hash FROM potential WHERE potential.hash = ?'
    UNIQUE_RUN_TRAINING = 'SELECT id, hash FROM training WHERE training.hash = ?'
    UNIQUE_RUN = '''
    SELECT run.id FROM run
              JOIN potential ON potential.id = run.potential_id
              JOIN training ON training.id = run.training_id
    WHERE name = ? AND potential.hash = ? AND training.hash = ? AND configuration = ?
                   AND start_time = ? AND (end_time = ? OR end_time IS NULL AND ? is NULL)
                   AND initial_parameters = ? AND indicies = ? AND bounds = ?
    '''

    INSERT_RUN_POTENTIAL = 'INSERT INTO potential (hash, schema) VALUES (?, ?)'
    INSERT_RUN_TRAINING = 'INSERT INTO training (hash, schema) VALUES (?, ?)'
    INSERT_RUN = 'INSERT INTO run (name, potential_id, training_id, configuration, start_time, end_time, initial_parameters, indicies, bounds) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
    INSERT_RUN_EVALUATION = 'INSERT INTO evaluation (run_id, parameters, sq_force_error, sq_stress_error, sq_energy_error, w_f, w_s, w_e) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'

    for run in src_dbm.connection.execute(SELECT_RUNS):
        # Potential
        query_result = src_dbm.connection.execute(SELECT_RUN_POTENTIAL, (run['id'],)).fetchone()
        potential_hash = query_result['hash']
        query = dest_dbm.connection.execute(UNIQUE_RUN_POTENTIAL, (potential_hash,)).fetchone()
        if query:
            potential_id = query['id']
        else:
            with dest_dbm.connection:
                cursor = dest_dbm.connection.execute(INSERT_RUN_POTENTIAL, (query_result['hash'], query_result['schema']))
                potential_id = cursor.lastrowid

        # Training
        query_result = src_dbm.connection.execute(SELECT_RUN_TRAINING, (run['id'],)).fetchone()
        training_hash = query_result['hash']
        query = dest_dbm.connection.execute(UNIQUE_RUN_TRAINING, (training_hash,)).fetchone()
        if query:
            training_id = query['id']
        else:
            with dest_dbm.connection:
                cursor = dest_dbm.connection.execute(INSERT_RUN_TRAINING, (query_result['hash'], query_result['schema']))
                training_id = cursor.lastrowid

        # Run
        query_result = src_dbm.connection.execute(SELECT_RUN, (run['id'],)).fetchone()
        query = dest_dbm.connection.execute(UNIQUE_RUN, (
            query_result['name'], potential_hash, training_hash, query_result['configuration'],
            query_result['start_time'], query_result['end_time'], query_result['end_time'],
            query_result['initial_parameters'], query_result['indicies'], query_result['bounds'])).fetchone()
        if query and only_unique:
            run_id = query['id']
        else:
            with dest_dbm.connection:
                cursor = dest_dbm.connection.execute(INSERT_RUN, (
                    query_result['name'], potential_id, training_id, query_result['configuration'],
                    query_result['start_time'], query_result['end_time'],
                    query_result['initial_parameters'], query_result['indicies'], query_result['bounds']))
                run_id = cursor.lastrowid

            # Evaluation
            num_evaluations = src_dbm.connection.execute(SELECT_RUN_EVALUATION_COUNT, (run['id'],)).fetchone()['num_evaluations']
            print('   adding run %d with %d evaluations' % (run['id'], num_evaluations))
            evaluation_limit = 1000
            for offset in range(0, num_evaluations, evaluation_limit):
                cursor = src_dbm.connection.execute(SELECT_RUN_EVALUATION, (run['id'], evaluation_limit, offset))
                evaluations = [(run_id, row['parameters'], row['sq_force_error'], row['sq_stress_error'], row['sq_energy_error'], row['w_f'], row['w_s'], row['w_e']) for row in cursor]
                with dest_dbm.connection:
                    dest_dbm.connection.executemany(INSERT_RUN_EVALUATION, evaluations)

            # labels
            labels = {row['key']: row['value'] for row in src_dbm.connection.execute(SELECT_RUN_LABELS, (run['id'],))}
            with dest_dbm.connection:
                _write_labels(dest_dbm, run_id, labels)


def list_runs(dbm):
    SELECT_RUNS = 'SELECT id FROM run'
    return [row['id'] for row in dbm.connection.execute(SELECT_RUNS)]


def list_evaluations(dbm, run_id):
    SELECT_EVALUATIONS = f'SELECT sq_force_error, sq_stress_error, sq_energy_error, w_f, w_s, w_e FROM evaluation WHERE run_id = {run_id}'
    df = pd.read_sql(SELECT_EVALUATIONS, dbm.connection)
    df['score'] = df['w_f'] * df['sq_force_error'] + df['w_s'] * df['sq_stress_error'] + df['w_e'] * df['sq_energy_error']
    return df


def run_summary(dbm, run_id):
    SELECT_RUN = 'SELECT id, name, potential_id, training_id, configuration, start_time, end_time, initial_parameters, indicies, bounds FROM run WHERE id = ?'

    SELECT_RUN_NUM_EVALUATIONS = 'SELECT count(*) FROM evaluation WHERE run_id = ?'
    SELECT_RUN_LAST_EVALUATIONS = '''
    SELECT (e.w_f * e.sq_force_error + e.w_s * e.sq_stress_error + e.w_e * e.sq_energy_error) AS score FROM evaluation e
    WHERE run_id = ?
    ORDER BY e.id DESC LIMIT 100
    '''

    run = dbm.connection.execute(SELECT_RUN, (run_id,)).fetchone()
    run_summary = {
        'algorithm': run['configuration']['spec']['algorithm']['name'],
        'initial_parameters': run['initial_parameters'],
    }
    num_evaluations = dbm.connection.execute(SELECT_RUN_NUM_EVALUATIONS, (run_id,)).fetchone()[0]
    run_summary.update({
        'steps': num_evaluations
    })
    last_scores = [row['score'] for row in dbm.connection.execute(SELECT_RUN_LAST_EVALUATIONS, (run_id,))]
    if last_scores:
        run_summary.update({
            'stats': {'mean': np.mean(last_scores), 'median': np.median(last_scores), 'min': np.min(last_scores)}
        })
        min_score = filter_evaluations(dbm, run_id=run_id, condition='best', limit=1).fetchone()
        run_summary.update({
            'final_parameters': min_score['parameters'],
            'min_score': min_score['score']
        })
    else:
        run_summary.update({
            'stats': {'mean': 0.0, 'median': 0.0, 'min': 0.0},
            'final_parameters': [],
            'min_score': 0.0
        })
    return run_summary
