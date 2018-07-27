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
    SELECT potential.schema, parameters, initial_parameters, indicies, bounds
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


def list_runs(dbm):
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
    SELECT_RUN_EVAL_AGG = '''
    SELECT run_id, count(*) as num_evaluations, min(value) as min_value
    FROM evaluation
    GROUP BY evaluation.run_id
    '''
    run_df = pd.read_sql(SELECT_RUNS, dbm.connection, index_col='run_id')
    eval_agg_df = pd.read_sql(SELECT_RUN_EVAL_AGG, dbm.connection, index_col='run_id')
    return pd.merge(run_df, eval_agg_df, on='run_id')


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
    features = run['features']
    # do something with run

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


# TODO
def filter_evaluations(dbm, potential=None, limit=10, condition='best', run_id=None, labels=None):
    pass


def filter_potentials(dbm, potential=None, limit=10, condition='best', run_id=None, labels=None):
    pass


def copy_database_to_database(src_dbm, dest_dbm, only_unique=False):
    pass


def run_summary(dbm, run_id):
    pass

# def filter_evaluations(dbm, potential=None, limit=10, condition='best', run_id=None, labels=None):
#     """Select a subset of evaluations. Currently only works on single
#     objective functions because "best" and "worst" are subjective in
#     multiobjecive functions.

#     Arguments:
#      - condition (str): best, random, worst

#     THIS IS THE REASON TO USE SQLALCHEMY QUERY BUILDER.... I HAVE LEARNED NOW
#     """

#     query = '''
#     SELECT run.id
#     FROM run {join_sql}
#     WHERE {where_sql}
#     '''

#     join_statement = []
#     where_statement = ['1=1']
#     query_arguments = []
#     if labels:
#         join_statement.extend([
#             'JOIN run_label ON run.id = run_label.run_id',
#             'JOIN label ON run_label.label_id = label.id'
#         ])
#         select_labels = []
#         for key, value in labels.items():
#             if not isinstance(key, str) or not isinstance(value, str):
#                 raise ValueError(f'key: {key} values: {values} for label must be strings')
#             select_labels.append('(label.key = ? AND label.value = ?)')
#             query_arguments.extend([key, value])
#         where_statement.append(' OR '.join(select_labels))
#         query += f"""
#         GROUP BY run.id
#         HAVING count = {len(labels)}
#         """

#     if run_id is not None:
#         if not isinstance(run_id, int):
#             raise ValueError('run_id must be integer')
#         where_statement.append('run.id = ?')
#         query_arguments.append(run_id)

#     if potential:
#         potential_str = json.dumps(potential.as_dict(with_parameters=False), sort_keys=True)
#         potential_hash = hashlib.md5(potential_str.encode('utf-8')).hexdigest()
#         join_statement.append('JOIN potential ON run.potential_id = potential.id')
#         where_statement.append('potential.hash = ?')
#         query_arguments.append(potential_hash)

#     # find all run ids that match selection
#     query = query.format(join_sql=' '.join(join_statement),
#                          where_sql=' AND '.join(where_statement))
#     run_ids = [row['id'] for row in dbm.connection.execute(query, query_arguments)]

#     if condition == 'best':
#         order_sql = 'score ASC'
#     elif condition == 'worst':
#         order_sql = 'score DESC'
#     elif condition == 'random':
#         order_sql = 'RANDOM()'
#     else:
#         raise ValueError('condition ordering not supported')

#     # pick subset of potentials
#     query = f'''
#     SELECT e.id, e.parameters, (e.w_f * e.sq_force_error + e.w_s * e.sq_stress_error + e.w_e * e.sq_energy_error) AS score FROM evaluation e
#     WHERE {' OR '.join(['e.run_id = ?' for _ in run_ids])}
#     ORDER BY {order_sql}
#     LIMIT {limit}
#     '''
#     return dbm.connection.execute(query, run_ids)


# def filter_potentials(dbm, potential=None, limit=10, condition='best', run_id=None, labels=None):
#     results = []
#     for row in filter_evaluations(dbm, potential, limit, condition, run_id, labels):
#         results.append({'potential': select_potential_from_evaluation(dbm, row['id']), 'score': row['score']})
#     return results




# def copy_database_to_database(src_dbm, dest_dbm, only_unique=False):
#     SELECT_RUNS = 'SELECT id FROM run'
#     SELECT_RUN = 'SELECT id, name, potential_hash, training_hash, configuration, start_time, end_time, initial_parameters, indicies, bounds, features, weights FROM run WHERE id = ?'
#     SELECT_RUN_LABELS = 'SELECT label.key, label.value FROM run_label JOIN label ON run_label.label_id = label.id WHERE run_label.run_id = ?'
#     SELECT_RUN_POTENTIAL = 'SELECT potential.hash, potential.schema FROM potential JOIN run ON run.potential_hash = potential.hash WHERE run.id = ?'
#     SELECT_RUN_TRAINING = 'SELECT training.hash, training.schema FROM training JOIN run ON run.training_hash = training.hash WHERE run.id = ?'
#     SELECT_RUN_EVALUATION_COUNT = 'SELECT count(*) as num_evaluations FROM evaluation WHERE run_id = ?'
#     SELECT_RUN_EVALUATION = '''
#     SELECT parameters, errors, value FROM evaluation
#     WHERE run_id = ? ORDER BY id LIMIT ? OFFSET ?
#     '''

#     UNIQUE_RUN_POTENTIAL = 'SELECT hash FROM potential WHERE potential.hash = ?'
#     UNIQUE_RUN_TRAINING = 'SELECT hash FROM training WHERE training.hash = ?'
#     UNIQUE_RUN = '''
#     SELECT run.id FROM run
#               JOIN potential ON potential.hash = run.potential_hash
#               JOIN training ON training.hash = run.training_hash
#     WHERE name = ? AND potential.hash = ? AND training.hash = ? AND configuration = ?
#                    AND start_time = ? AND (end_time = ? OR end_time IS NULL AND ? is NULL)
#                    AND initial_parameters = ? AND indicies = ? AND bounds = ?
#     '''

#     INSERT_RUN_POTENTIAL = 'INSERT INTO potential (hash, schema) VALUES (?, ?)'
#     INSERT_RUN_TRAINING = 'INSERT INTO training (hash, schema) VALUES (?, ?)'
#     INSERT_RUN = 'INSERT INTO run (name, potential_id, training_id, configuration, start_time, end_time, initial_parameters, indicies, bounds) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
#     INSERT_RUN_EVALUATION = 'INSERT INTO evaluation (run_id, parameters, sq_force_error, sq_stress_error, sq_energy_error, w_f, w_s, w_e) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'

#     for run in src_dbm.connection.execute(SELECT_RUNS):
#         # Potential
#         query_result = src_dbm.connection.execute(SELECT_RUN_POTENTIAL, (run['id'],)).fetchone()
#         potential_hash = query_result['hash']
#         query = dest_dbm.connection.execute(UNIQUE_RUN_POTENTIAL, (potential_hash,)).fetchone()
#         if query:
#             potential_id = query['id']
#         else:
#             with dest_dbm.connection:
#                 cursor = dest_dbm.connection.execute(INSERT_RUN_POTENTIAL, (query_result['hash'], query_result['schema']))
#                 potential_id = cursor.lastrowid

#         # Training
#         query_result = src_dbm.connection.execute(SELECT_RUN_TRAINING, (run['id'],)).fetchone()
#         training_hash = query_result['hash']
#         query = dest_dbm.connection.execute(UNIQUE_RUN_TRAINING, (training_hash,)).fetchone()
#         if query:
#             training_id = query['id']
#         else:
#             with dest_dbm.connection:
#                 cursor = dest_dbm.connection.execute(INSERT_RUN_TRAINING, (query_result['hash'], query_result['schema']))
#                 training_id = cursor.lastrowid

#         # Run
#         query_result = src_dbm.connection.execute(SELECT_RUN, (run['id'],)).fetchone()
#         query = dest_dbm.connection.execute(UNIQUE_RUN, (
#             query_result['name'], potential_hash, training_hash, query_result['configuration'],
#             query_result['start_time'], query_result['end_time'], query_result['end_time'],
#             query_result['initial_parameters'], query_result['indicies'], query_result['bounds'])).fetchone()
#         if query and only_unique:
#             run_id = query['id']
#         else:
#             with dest_dbm.connection:
#                 cursor = dest_dbm.connection.execute(INSERT_RUN, (
#                     query_result['name'], potential_id, training_id, query_result['configuration'],
#                     query_result['start_time'], query_result['end_time'],
#                     query_result['initial_parameters'], query_result['indicies'], query_result['bounds']))
#                 run_id = cursor.lastrowid

#             # Evaluation
#             num_evaluations = src_dbm.connection.execute(SELECT_RUN_EVALUATION_COUNT, (run['id'],)).fetchone()['num_evaluations']
#             print('   adding run %d with %d evaluations' % (run['id'], num_evaluations))
#             evaluation_limit = 1000
#             for offset in range(0, num_evaluations, evaluation_limit):
#                 cursor = src_dbm.connection.execute(SELECT_RUN_EVALUATION, (run['id'], evaluation_limit, offset))
#                 evaluations = [(run_id, row['parameters'], row['sq_force_error'], row['sq_stress_error'], row['sq_energy_error'], row['w_f'], row['w_s'], row['w_e']) for row in cursor]
#                 with dest_dbm.connection:
#                     dest_dbm.connection.executemany(INSERT_RUN_EVALUATION, evaluations)

#             # labels
#             labels = {row['key']: row['value'] for row in src_dbm.connection.execute(SELECT_RUN_LABELS, (run['id'],))}
#             with dest_dbm.connection:
#                 _write_labels(dest_dbm, run_id, labels)


# def run_summary(dbm, run_id):
#     SELECT_RUN = 'SELECT id, name, potential_id, training_id, configuration, start_time, end_time, initial_parameters, indicies, bounds FROM run WHERE id = ?'

#     SELECT_RUN_NUM_EVALUATIONS = 'SELECT count(*) FROM evaluation WHERE run_id = ?'
#     SELECT_RUN_LAST_EVALUATIONS = '''
#     SELECT (e.w_f * e.sq_force_error + e.w_s * e.sq_stress_error + e.w_e * e.sq_energy_error) AS score FROM evaluation e
#     WHERE run_id = ?
#     ORDER BY e.id DESC LIMIT 100
#     '''

#     run = dbm.connection.execute(SELECT_RUN, (run_id,)).fetchone()
#     run_summary = {
#         'algorithm': run['configuration']['spec']['algorithm']['name'],
#         'initial_parameters': run['initial_parameters'],
#     }
#     num_evaluations = dbm.connection.execute(SELECT_RUN_NUM_EVALUATIONS, (run_id,)).fetchone()[0]
#     run_summary.update({
#         'steps': num_evaluations
#     })
#     last_scores = [row['score'] for row in dbm.connection.execute(SELECT_RUN_LAST_EVALUATIONS, (run_id,))]
#     if last_scores:
#         run_summary.update({
#             'stats': {'mean': np.mean(last_scores), 'median': np.median(last_scores), 'min': np.min(last_scores)}
#         })
#         min_score = filter_evaluations(dbm, run_id=run_id, condition='best', limit=1).fetchone()
#         run_summary.update({
#             'final_parameters': min_score['parameters'],
#             'min_score': min_score['score']
#         })
#     else:
#         run_summary.update({
#             'stats': {'mean': 0.0, 'median': 0.0, 'min': 0.0},
#             'final_parameters': [],
#             'min_score': 0.0
#         })
#     return run_summary
