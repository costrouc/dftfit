import random
import json
import logging

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
        logger = logging.getLogger(__name__)

        # Name and Labels
        self.run_name = self.schema['metadata'].get('name')
        self.run_labels = self.schema['metadata'].get('labels')

        # Seed
        self.seed = self.schema['spec'].get('seed', random.randint(0, 1_000_000_000))

        # Database
        self.dbm = None
        self.db_write_interval = self.schema['spec'].get('database', {}).get('interval', 10)
        if self.schema['spec'].get('database', {}).get('filename'):
            database_filename = os.path.expanduser(self.schema['spec']['database']['filename'])
            logger.info('(configuration) using sqlite database %s' % database_filename)
            database_directory, filename = os.path.split(database_filename)
            os.makedirs(database_directory, exist_ok=True)
            self.dbm = DatabaseManager(database_filename)

        # Training
        self.training_kwargs = self.schema['spec'].get('training', {
            'cache_filename': '~/.cache/dftfit/cache.db'})

        # Algorithm
        _algorithm_kwargs = self.schema['spec'].get('algorithm', {
            'name': 'pygmo.sade',
            'steps': 10,
            'population': 10,
            'include_initial_guess': False
        })
        self.algorithm = _algorithm_kwargs['name']
        self.steps = _algorithm_kwargs['steps']
        self.population = _algorithm_kwargs['population']
        self.include_initial_guess = _algorithm_kwargs.get('include_initial_guess', False)
        self.algorithm_kwargs = {k:v for k,v in _algorithm_kwargs.items() if k not in {'name', 'steps', 'population', 'include_initial_guess'}}

        # Problem
        _problem_kwargs = self.schema['spec'].get('problem', {
            'calculator': 'lammps_cython',
            'num_workers': 1,
            'weights': {'force': 0.6, 'stress': 0.2, 'energy': 0.2}
        })
        self.features = []
        self.weights = []
        for feature in sorted(_problem_kwargs['weights']):
            self.features.append(feature)
            self.weights.append(_problem_kwargs['weights'][feature])
        self.problem_kwargs = {k:v for k,v in _problem_kwargs.items() if k not in {'weights'}}

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
