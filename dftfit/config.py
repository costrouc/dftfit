import random
import json

import yaml
import os

from .logging import init_logging
from .db import DatabaseManager
from .schema import ConfigurationSchema


class Configuration:
    def __init__(self, schema):
        schema_load, errors = ConfigurationSchema().load(schema)
        self.schema = schema_load

        # Logging
        init_logging(self.schema['spec'].get('logging', 'WARNING'))

        # Name and Labels
        self.run_name = self.schema['metadata'].get('name')
        self.run_labels = self.schema['metadata'].get('labels')

        # Seed
        self.seed = self.schema['spec'].get('seed', random.randint(0, 1_000_000_000))

        # Database
        self.dbm = None
        if 'database' in self.schema['spec']:
            database_filename = os.path.expanduser(self.schema['spec']['database'])
            database_directory, filename = os.path.split(database_filename)
            os.makedirs(database_directory, exist_ok=True)
            self.dbm = DatabaseManager(database_filename)

        # Training
        self.training_kwargs = self.schema['spec'].get('training', {
            'cache_filename': '~/.cache/dftfit/cache.db'})

        # Algorithm
        _algorithm_kwargs= self.schema['spec'].get('algorithm', {})
        self.algorithm = _algorithm_kwargs.get('name', 'pygmo.de')
        self.steps = self.schema['spec'].get('steps', 10)
        self.population = self.schema['spec'].get('population', 5)
        self.algorithm_kwargs = {k:v for k,v in _algorithm_kwargs.items() if k != 'name'}

        # Problem
        self.problem_kwargs = self.schema['spec'].get('problem', {})

    @classmethod
    def from_file(cls, filename, format=None):
        if format not in {'json', 'yaml'}:
            if filename.endswith('json'):
                format = 'json'
            elif filename.endswith('yaml') or filename.endswith('yml'):
                format = 'yaml'
            else:
                raise ValueError('unrecognized filetype from filename %s' % filename)

        if format == 'json':
            with open(filename) as f:
                return cls(json.load(f))
        elif format in {'yaml', 'yml'}:
            with open(filename) as f:
                return cls(yaml.load(f))

    def __str__(self):
        return json.dumps(self.schema, sort_keys=True, indent=4)
