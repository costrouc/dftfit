import json
import hashlib
import datetime as dt


def write_potential(dbm, potential):
    potential_str = json.dumps(potential.as_dict(with_parameters=False), sort_keys=True)
    potential_hash = hashlib.md5(potential_str.encode('utf-8')).hexdigest()

    with dbm.connection:
        result = dbm.connection.execute(
            'SELECT id FROM potential WHERE potential.id = ?',
            (potential_hash,)).fetchone()
        if result:
            return result['id']

        cursor = dbm.connection.execute(
            'INSERT INTO potential (id, schema) VALUES (?, ?)',
            (potential_hash, potential_str)
        )
        return cursor.lastrowid


def write_run_initial(dbm, potential):
    potential_id = write_potential(dbm, potential)

    with dbm.connection:
        cursor = dbm.connection.execute('''
        INSERT INTO run (potential_id, start_time, initial_parameters, indicies, bounds)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            potential_id,
            dt.datetime.now(),
            potential.parameters.tolist(),
            potential.optimization_parameter_indicies.tolist(),
            potential.optimization_bounds.tolist()
        ))
        return potential_id, cursor.lastrowid


def write_run_final(dbm, run_id):
    with dbm.connection:
        cursor = dbm.connection.execute('UPDATE run SET end_time = ? WHERE id = ? AND end_time IS NULL', (dt.datetime.now(), run_id))


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
