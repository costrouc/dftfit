""" Handles collection of trial and testing data.

Has a caching layer as to speed up future runs
"""
import json
import shelve
import os

import yaml

from .schema import TrainingSchema
from .io import MTKReader


class Training:
    def __init__(self, schema, cache_filename=None):
        schema_load, errors = TrainingSchema().load(schema)
        self.schema = schema_load
        self._gather_calculations(cache_filename=cache_filename)

    def _gather_calculations(self, cache_filename=None):
        self._calculations = []
        for calculation in self.schema['spec']:
            if calculation['type'] == 'mattoolkit':
                self._calculations.extend(self.download_mattoolkit_calculations(calculation['selector'], cache_filename=cache_filename))

    @property
    def calculations(self):
        return self._calculations

    def __iter__(self):
        return iter(self._calculations)

    def __len__(self):
        return len(self._calculations)

    def download_mattoolkit_calculations(self, selector, cache_filename=None):
        from mattoolkit.api import CalculationResourceList

        if cache_filename:
            cache_directory, filename = os.path.split(cache_filename)
            os.makedirs(cache_directory, exist_ok=True)
            key = f'mattoolkit.calculation.' + '.'.join(selector['labels'])
            with shelve.open(cache_filename) as cache:
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
        return [MTKReader(calc_id, cache_filename=cache_filename) for calc_id in calc_ids]

    @classmethod
    def from_file(cls, filename, format=None, **kwargs):
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
                return cls(yaml.load(f), **kwargs)

    def __str__(self):
        return json.dumps(self.schema, sort_keys=True, indent=4)
