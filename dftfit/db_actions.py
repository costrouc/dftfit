import json
import hashlib
import datetime as dt


def _write_potential(dbm, potential):
    potential_str = json.dumps(potential.as_dict(with_parameters=False), sort_keys=True)
    potential_hash = hashlib.md5(potential_str.encode('utf-8')).hexdigest()

    result = dbm.connection.execute(
        'SELECT id FROM potential WHERE potential.id = ?',
        (potential_hash,)).fetchone()
    if result:
        return result['id']

    cursor = dbm.connection.execute(
        'INSERT INTO potential (id, schema) VALUES (?, ?)',
        (potential_hash, potential.as_dict(with_parameters=False))
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
        cursor = dbm.connection.execute('''
        INSERT INTO run (name, potential_id, training, configuration, start_time, initial_parameters, indicies, bounds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            configuration.run_name,
            potential_id,
            training.schema,
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
