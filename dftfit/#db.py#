import sqlite3 as sqlite
import json
import datetime as dt


POTENTIAL_TABLE = """
CREATE TABLE IF NOT EXISTS potential (
    id     INTEGER PRIMARY KEY,
    hash   TEXT NOT NULL,
    schema JSON NOT NULL,

    UNIQUE (hash) ON CONFLICT ROLLBACK
)
"""


TRAINING_TABLE = """
CREATE TABLE IF NOT EXISTS training (
    id     INTEGER PRIMARY KEY,
    hash   TEXT NOT NULL,
    schema JSON NOT NULL,

    UNIQUE (hash) ON CONFLICT ROLLBACK
)
"""


RUN_TABLE = """
CREATE TABLE IF NOT EXISTS run (
    id                 INTEGER PRIMARY KEY,
    name               TEXT,
    potential_id       INTEGER NOT NULL,
    training_id        INTEGER NOT NULL,
    configuration      JSON,
    start_time         DATETIME NOT NULL,
    end_time           DATETIME,
    initial_parameters JSON NOT NULL,
    indicies           JSON NOT NULL,
    bounds             JSON NOT NULL,

    FOREIGN KEY(potential_id) REFERENCES potential(id),
    FOREIGN KEY(training_id) REFERENCES training(id)
)
"""

RUN_LABEL_TABLE = """
CREATE TABLE IF NOT EXISTS run_label (
    run_id      INTEGER NOT NULL,
    label_id    INTEGER NOT NULL,

    PRIMARY KEY(run_id, label_id),
    FOREIGN KEY(run_id) REFERENCES run(id),
    FOREIGN KEY(label_id) REFERENCES label(id)
)
"""

LABEL_TABLE = """
CREATE TABLE IF NOT EXISTS label (
    id        INTEGER PRIMARY KEY,
    key       TEXT NOT NULL,
    value     TEXT NOT NULL,

    UNIQUE(key, value) ON CONFLICT ROLLBACK
)
"""

EVALUATION_TABLE = """
CREATE TABLE IF NOT EXISTS evaluation (
    id                 INTEGER PRIMARY KEY,
    run_id             INTEGER NOT NULL,
    parameters         JSON NOT NULL,
    sq_force_error     REAL NOT NULL,
    sq_stress_error    REAL NOT NULL,
    sq_energy_error    REAL NOT NULL,
    w_f                REAL NOT NULL,
    w_s                REAL NOT NULL,
    w_e                REAL NOT NULL,

    FOREIGN KEY(run_id) REFERENCES run(id)
)
"""


class DatabaseManager:
    def __init__(self, filename=None):
        self._connection = sqlite.connect(filename or ':memory:',
                                          detect_types=sqlite.PARSE_DECLTYPES)
        self._connection.row_factory = sqlite.Row
        self.register_types()
        self.create_tables()

    @staticmethod
    def adapt_json(d):
        return (json.dumps(d, sort_keys=True)).encode()

    @staticmethod
    def convert_json(data):
        return json.loads(data.decode())

    @staticmethod
    def adapt_datetime(datetime):
        return (datetime.strftime('%Y-%m-%d %H:%M:%S')).encode()

    @staticmethod
    def convert_datetime(data):
        return dt.datetime.strptime(data.decode(), '%Y-%m-%d %H:%M:%S')

    def register_types(self):
        sqlite.register_adapter(dt.datetime, self.adapt_datetime)
        sqlite.register_adapter(dict, self.adapt_json)
        sqlite.register_adapter(list, self.adapt_json)
        sqlite.register_adapter(tuple, self.adapt_json)
        sqlite.register_converter('datetime', self.convert_datetime)
        sqlite.register_converter('json', self.convert_json)

    def create_tables(self):
        self.connection.execute(POTENTIAL_TABLE)
        self.connection.execute(TRAINING_TABLE)
        self.connection.execute(RUN_TABLE)
        self.connection.execute(RUN_LABEL_TABLE)
        self.connection.execute(LABEL_TABLE)
        self.connection.execute(EVALUATION_TABLE)

    @property
    def connection(self):
        return self._connection
