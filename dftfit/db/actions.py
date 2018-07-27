import json
import datetime as dt


def _write_potential(dbm, potential):
    potential_hash = potential.md5hash
    dbm.connection.execute("""
    INSERT OR REPLACE INTO potential (hash, schema)
    VALUES (?, ?)
    """, (potential_hash, potential.as_dict(with_parameters=False)))
    return potential_hash


def _write_training(dbm, training):
    training_hash = training.md5hash
    dbm.connection.execute("""
    INSERT OR REPLACE INTO training (hash, schema)
    VALUES (?, ?)
    """, (training_hash, training.schema))
    return training_hash


def _write_labels(dbm, run_id, labels):
    for key, value in labels.items():
        result = dbm.connection.execute('''
        SELECT id FROM label WHERE label.key = ? AND label.value = ?
        ''', (key, value)).fetchone()

        if result:
            label_id = result['id']
        else:
            cursor = dbm.connection.execute('''
            INSERT INTO label (key, value) VALUES (?, ?)
            ''', (key, value))
            label_id = cursor.lastrowid

        cursor = dbm.connection.execute('''
        INSERT INTO run_label (run_id, label_id) VALUES (?, ?)
        ''', (run_id, label_id))


def write_run_initial(dbm, potential, training, configuration):
    with dbm.connection:
        potential_hash = _write_potential(dbm, potential)
        training_hash = _write_training(dbm, training)
        cursor = dbm.connection.execute('''
        INSERT INTO run (
              name, potential_hash, training_hash,
              configuration, start_time,
              initial_parameters, indicies, bounds,
              features, weights
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            configuration.run_name,
            potential_hash,
            training_hash,
            configuration.schema,
            dt.datetime.utcnow(),
            potential.parameters.tolist(),
            potential.optimization_parameter_indicies.tolist(),
            potential.optimization_bounds.tolist(),
            configuration.features,
            configuration.weights
        ))
        run_id = cursor.lastrowid
        _write_labels(dbm, run_id, configuration.run_labels)
        return potential_hash, run_id


def write_run_final(dbm, run_id):
    with dbm.connection:
        dbm.connection.execute('''
        UPDATE run SET end_time = ?
        WHERE id = ? AND end_time IS NULL
        ''', (dt.datetime.utcnow(), run_id))


def write_evaluation(dbm, run_id, potential, errors, value):
    with dbm.connection:
        dbm.connection.execute('''
        INSERT INTO evaluation (run_id, parameters, errors, value)
        VALUES (?, ?, ?, ?)
        ''', (run_id, potential.optimization_parameters.tolist(), errors, value))


def write_evaluations_batch(dbm, run_id, eval_batch):
    with dbm.connection:
        evaluations = [(run_id, potential.optimization_parameters.tolist(), errors, value) for potential, errors, value in eval_batch]
        dbm.connection.executemany('''
        INSERT INTO evaluation (run_id, parameters, errors, value)
        VALUES (?, ?, ?, ?)
        ''', evaluations)
