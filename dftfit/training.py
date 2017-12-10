""" Handles collection of trial and testing data.

Has a caching layer as to speed up future runs
"""
import json
import shelve
import os

import yaml

from .schema import TrainingSchema
from .io import MTKReader
from .config import CACHE_FILENAME


class Training:
    def __init__(self, schema, use_cache=True):
        schema_load, errors = TrainingSchema().load(schema)
        self.schema = schema_load
        self._gather_calculations(use_cache=use_cache)

    def _gather_calculations(self, use_cache=True):
        self._calculations = []
        for calculation in self.schema['spec']:
            if calculation['type'] == 'mattoolkit':
                self._calculations.extend(self.download_mattoolkit_calculations(calculation['selector'], use_cache=True))

    @property
    def calculations(self):
        return self._calculations

    def __iter__(self):
        return iter(self._calculations)

    def __len__(self):
        return len(self._calculations)

    def download_mattoolkit_calculations(self, selector, use_cache=True):
        from mattoolkit.api import CalculationResourceList

        if use_cache:
            cache_directory = os.path.expanduser('~/.cache/dftfit/')
            os.makedirs(cache_directory, exist_ok=True)
            key = f'mattoolkit.calculation.' + '.'.join(selector['labels'])
            with shelve.open(os.path.join(cache_directory, CACHE_FILENAME)) as cache:
                if key in cache:
                    calc_ids = cache[key]
                else:
                    calculations = CalculationResourceList()
                    calculations.get(params={'labels': selector['labels']})
                    calc_ids = [c.id for c in calculations.items]
                    cache[key] = calc_ids
        else:
            calculations = CalculationResourceList()
            calculations.get(params={'labels': selector['labels']})
            calc_ids = [c.id for c in calculations.items]
        return [MTKReader(calc_id, use_cache=use_cache) for calc_id in calc_ids]

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
