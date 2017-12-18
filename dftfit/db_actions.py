import json
import hashlib
import datetime as dt

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


def filter_potentials(dbm, potential, limit=10, condition='best', run_id=None, labels=None):
    """Select a subset of evaluations. Currently only works on single
    objective functions because "best" and "worst" are subjective in
    multiobjecive functions.

    Arguments:
     - condition (str): best, random, worst

    THIS IS THE REASON TO USE SQLALCHEMY QUERY BUILDER.... I HAVE LEARNED NOW
    """
    potential_str = json.dumps(potential.as_dict(with_parameters=False), sort_keys=True)
    potential_hash = hashlib.md5(potential_str.encode('utf-8')).hexdigest()

    query = '''
    SELECT DISTINCT run.id, count(*) as count
    FROM run {join_sql}
    WHERE {where_sql}
    '''

    join_statement = []
    where_statement = []
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

    join_statement.append('JOIN potential ON run.potential_id = potential.id')
    where_statement.append('potential.hash = ?')
    query_arguments.append(potential_hash)

    if condition == 'best':
        order_sql = 'score ASC'
    elif condition == 'worst':
        order_sql = 'score DESC'
    elif condition == 'random':
        order_sql = 'RANDOM()'
    else:
        raise ValueError('condition ordering not supported')

    # find all run ids that match selection
    query = query.format(join_sql=' '.join(join_statement),
                         where_sql=' AND '.join(where_statement))

    run_ids = [row['id'] for row in dbm.connection.execute(query, query_arguments)]
    # pick subset of potentials
    query = f'''
    SELECT e.parameters, (e.w_f * e.sq_force_error + e.w_s * e.sq_stress_error + e.w_e * e.sq_energy_error) AS score FROM evaluation e
    WHERE {' OR '.join(['e.run_id = ?' for _ in run_ids])}
    ORDER BY {order_sql}
    LIMIT {limit}
    '''
    results = []
    for row in dbm.connection.execute(query, run_ids):
        tmp_potential = potential.copy()
        tmp_potential.optimization_parameters = row['parameters']
        results.append({'potential': tmp_potential, 'score': row['score']})
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

    # TODO but the information is there
    parameter_index = 0
    initial_parameters = result['initial_parameters']

    def _walk(value): # Ordered traversal of dictionary
        if isinstance(value, dict):
            for key in sorted(value.keys()):
                if isinstance(value[key], str) and value[key] == 'FloatParameter':
                    value[key] = {'initial': 0.0}
                else:
                    _walk(value[key])
        elif isinstance(value, (list)):
            for i, item in enumerate(value):
                if isinstance(item, str) and item == 'FloatParameter':
                    value[i] = {'initial': 0.0}
                else:
                    _walk(item)
    potential_schema = result['schema']
    _walk(potential_schema)

    print(result['initial_parameters'])
    print(result['indicies'])
    print(result['parameters'])
    print(result['bounds'])

    # potential = Potential(potential_schema)
    # potential._bounds
