import pandas as pd
import numpy as np

from ..potential import Potential


def potential_from_evaluation(dbm, evaluation_id):
    """Construct potential from single evaluation id

    Parameters
    ----------
    dbm: dftfit.db.table.DatabaseManager
       dftfit database access class
    evaluation_id: int
       integer representing the id of the evaluation

    Returns
    -------
    dftfit.potential.Potential
       potential representing the single evaluation
    """
    result = dbm.connection.execute('''
    SELECT potential.schema, evaluation.parameters, run.initial_parameters, run.indicies, run.bounds
    FROM evaluation
        JOIN run ON run.id = evaluation.run_id
        JOIN potential ON potential.hash = run.potential_hash
    WHERE evaluation.id = ?
    ''', (evaluation_id,)).fetchone()
    if result is None:
        raise ValueError(f'evaluation_id {evaluation_id} does not exist')

    return Potential.from_run_evaluation(
        result['schema'],
        result['initial_parameters'],
        result['indicies'], result['parameters'], result['bounds'])


def list_runs(dbm, parameters=True, stats=True):
    """Create pandas dataframe of runs

    Parameters
    ----------
    dbm: dftfit.db.table.DatabaseManager
       dftfit database access class

    Returns
    -------
    pandas.DataFrame:
        dataframe with fields: id, name, potential_hash, training_hash,
        start_time, end_time, features, weights, num_evaluations, min_value
    """
    SELECT_RUNS = '''
    SELECT id as run_id, name,
           potential_hash, training_hash,
           start_time, end_time, features, weights
    FROM run
    '''
    run_df = pd.read_sql(SELECT_RUNS, dbm.connection, index_col='run_id')

    if stats:
        SELECT_RUN_EVAL_AGG_MIN_COUNT = '''
        SELECT run_id, count(*) as num_evaluations, min(value) as min_value
        FROM evaluation
        GROUP BY run_id
        '''
        run_df = pd.merge(run_df, pd.read_sql(SELECT_RUN_EVAL_AGG_MIN_COUNT, dbm.connection, index_col='run_id'), on='run_id')

        # SELECT_RUN_EVAL_AGG_MIN_MEAN = '''
        # SELECT run_id, min(value) as last_100_min_value, avg(value) as last_100_mean_value
        # FROM evaluation
        # GROUP BY run_id
        # ORDER BY id DESC LIMIT 100
        # '''
        # run_df = pd.merge(run_df, pd.read_sql(SELECT_RUN_EVAL_AGG_MIN_MEAN, dbm.connection, index_col='run_id'), on='run_id')

    if parameters:
        parameter_values = []
        for run_id in run_df.index.values:
            SELECT_RUN_MIN_VALUE_PARAMETERS = '''
            SELECT id, parameters
            FROM evaluation
            WHERE run_id = {}
            ORDER BY id DESC LIMIT 1
            '''.format(run_id)
            cursor = dbm.connection.execute(SELECT_RUN_MIN_VALUE_PARAMETERS).fetchone()
            parameter_values.append({'run_id': run_id, 'final_parameters': cursor['parameters']})
        run_df = pd.merge(run_df, pd.DataFrame(parameter_values), on='run_id')

    return run_df


def list_run_evaluations(dbm, run_id, min_evaluation=None):
    """Create pandas dataframe of evaluations with run_id

    Parameters
    ----------
    dbm: dftfit.db.table.DatabaseManager
       dftfit database access class
    run_id: int
       identifier of run
    min_evaluation: int
       used a filter to select all evaluations since certain point

    Returns
    -------
    pandas.DataFrame:
        dataframe with fields: evaluation_id, potential parameters,
        all features with error, and value
    """
    run = dbm.connection.execute(
        'SELECT features FROM run WHERE id = ?', (run_id,)).fetchone()
    if run is None:
        raise ValueError('run with run_id {} does not exist'.format(run_id))
    features = run['features']

    SELECT_EVALUATIONS = '''
    SELECT id as evaluation_id, parameters, errors, value
    FROM evaluation
    WHERE run_id = {}
    '''.format(run_id)
    df = pd.read_sql(SELECT_EVALUATIONS, dbm.connection, index_col='evaluation_id')
    errors = np.array(df['errors'].values.tolist())
    for i, feature in enumerate(features):
        df[feature] = errors[:, i]
    return df.drop('errors', axis=1)


def filter_evaluations(dbm, potential=None, limit=10, condition='best', run_id=None, labels=None, include_potentials=False):
    cursor = dbm.connection.execute('SELECT id FROM run')
    run_ids = {_['id'] for _ in cursor}

    if potential:
        RUNS_WITH_POTENTIAL = """
        SELECT run_id
        FROM run
        WHERE run.potential_hash = ?
        """
        cursor = dbm.connection.execute(RUNS_WITH_POTENTIAL, (potential.md5hash,))
        potential_run_ids = {_['run_id'] for _ in cursor}
        run_ids = potential_run_ids & run_ids

    if run_id:
        run_ids = run_ids & {run_id}

    if labels:
        arguments = []
        for key, value in labels:
            arguments.extend([key, value])

        RUN_ID_FROM_LABEL_IDS = """
        SELECT run_id
        FROM run_label
        JOIN label ON run_label.label_id = label.id
        WHERE {}
        GROUP BY run_id
        HAVING count = {}
        """.format(
            ' OR '.join(['(label.key = ? AND label.value = ?)']*len(labels)),
            len(labels)
        )
        cursor = dbm.connection.execute(RUN_ID_FROM_LABEL_IDS, arguments)
        label_run_ids = {_['run_id'] for _ in cursor}
        run_ids = label_run_ids & run_ids

    if len(run_ids) == 0:
        return pd.DataFrame()

    if condition != 'best':
        raise ValueError('only know how to sort on condition best right now')

    SELECT_EVALUATIONS = '''
    SELECT id as evaluation_id, run_id, parameters, errors, value
    FROM evaluation
    WHERE {}
    ORDER BY value LIMIT {}
    '''.format(' OR '.join(['run_id = %d' % run_id for run_id in run_ids]), limit)
    df = pd.read_sql(SELECT_EVALUATIONS, dbm.connection, index_col='evaluation_id')

    if include_potentials:
        eval_potentials = []
        for eval_id in df.index.values:
            eval_potentials.append({'evaluation_id': eval_id, 'potential': potential_from_evaluation(dbm, int(eval_id))})
        df = pd.merge(df, pd.DataFrame(eval_potentials), on='evaluation_id')

    return df


def copy_database_to_database(src_dbm, dest_dbm, only_unique=False):
    SELECT_RUNS = 'SELECT id FROM run'
    SELECT_RUN = 'SELECT id, name, potential_hash, training_hash, configuration, start_time, end_time, initial_parameters, indicies, bounds, features, weights FROM run WHERE id = ?'
    SELECT_RUN_LABELS = 'SELECT label.key, label.value FROM run_label JOIN label ON run_label.label_id = label.id WHERE run_label.run_id = ?'
    SELECT_RUN_POTENTIAL = 'SELECT potential.hash, potential.schema FROM potential JOIN run ON run.potential_hash = potential.hash WHERE run.id = ?'
    SELECT_RUN_TRAINING = 'SELECT training.hash, training.schema FROM training JOIN run ON run.training_hash = training.hash WHERE run.id = ?'
    SELECT_RUN_EVALUATION_COUNT = 'SELECT count(*) as num_evaluations FROM evaluation WHERE run_id = ?'
    SELECT_RUN_EVALUATION = '''
    SELECT parameters, errors, value FROM evaluation
    WHERE run_id = ? ORDER BY id LIMIT ? OFFSET ?
    '''

    UNIQUE_RUN_POTENTIAL = 'SELECT hash FROM potential WHERE potential.hash = ?'
    UNIQUE_RUN_TRAINING = 'SELECT hash FROM training WHERE training.hash = ?'
    UNIQUE_RUN = '''
    SELECT run.id FROM run
              JOIN potential ON potential.hash = run.potential_hash
              JOIN training ON training.hash = run.training_hash
    WHERE name = ? AND potential.hash = ? AND training.hash = ? AND configuration = ?
                   AND start_time = ? AND (end_time = ? OR end_time IS NULL AND ? is NULL)
                   AND initial_parameters = ? AND indicies = ? AND bounds = ? AND features = ? AND weights = ?
    '''

    INSERT_RUN_POTENTIAL = 'INSERT INTO potential (hash, schema) VALUES (?, ?)'
    INSERT_RUN_TRAINING = 'INSERT INTO training (hash, schema) VALUES (?, ?)'
    INSERT_RUN = 'INSERT INTO run (name, potential_hash, training_hash, configuration, start_time, end_time, initial_parameters, indicies, bounds, features, weights) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    INSERT_RUN_EVALUATION = 'INSERT INTO evaluation (run_id, parameters, errors, value) VALUES (?, ?, ?, ?)'

    for run in src_dbm.connection.execute(SELECT_RUNS):
        # Potential
        query_result = src_dbm.connection.execute(SELECT_RUN_POTENTIAL, (run['id'],)).fetchone()
        potential_hash = query_result['hash']
        query = dest_dbm.connection.execute(UNIQUE_RUN_POTENTIAL, (potential_hash,)).fetchone()
        if not query:
            with dest_dbm.connection:
                cursor = dest_dbm.connection.execute(INSERT_RUN_POTENTIAL, (query_result['hash'], query_result['schema']))

        # Training
        query_result = src_dbm.connection.execute(SELECT_RUN_TRAINING, (run['id'],)).fetchone()
        training_hash = query_result['hash']
        query = dest_dbm.connection.execute(UNIQUE_RUN_TRAINING, (training_hash,)).fetchone()
        if not query:
            with dest_dbm.connection:
                cursor = dest_dbm.connection.execute(INSERT_RUN_TRAINING, (query_result['hash'], query_result['schema']))

        # Run
        query_result = src_dbm.connection.execute(SELECT_RUN, (run['id'],)).fetchone()
        query = dest_dbm.connection.execute(UNIQUE_RUN, (
            query_result['name'], potential_hash, training_hash, query_result['configuration'],
            query_result['start_time'], query_result['end_time'], query_result['end_time'],
            query_result['initial_parameters'], query_result['indicies'], query_result['bounds'], query_result['features'], query_result['weights'])).fetchone()
        if query and only_unique:
            run_id = query['id']
        else:
            with dest_dbm.connection:
                cursor = dest_dbm.connection.execute(INSERT_RUN, (
                    query_result['name'], potential_hash, training_hash, query_result['configuration'],
                    query_result['start_time'], query_result['end_time'],
                    query_result['initial_parameters'], query_result['indicies'], query_result['bounds'], query_result['features'], query_result['weights']))
                run_id = cursor.lastrowid

            # Evaluation
            num_evaluations = src_dbm.connection.execute(SELECT_RUN_EVALUATION_COUNT, (run['id'],)).fetchone()['num_evaluations']
            print('   adding run %d with %d evaluations' % (run['id'], num_evaluations))
            evaluation_limit = 1000
            for offset in range(0, num_evaluations, evaluation_limit):
                cursor = src_dbm.connection.execute(SELECT_RUN_EVALUATION, (run['id'], evaluation_limit, offset))
                evaluations = [(run_id, row['parameters'], row['errors'], row['value']) for row in cursor]
                with dest_dbm.connection:
                    dest_dbm.connection.executemany(INSERT_RUN_EVALUATION, evaluations)

            # labels
            labels = {row['key']: row['value'] for row in src_dbm.connection.execute(SELECT_RUN_LABELS, (run['id'],))}
            with dest_dbm.connection:
                _write_labels(dest_dbm, run_id, labels)
