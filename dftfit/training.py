""" Handles collection of trial and testing data.

Has a caching layer as to speed up future runs
"""
import json

import yaml

from .schema import TrainingSchema
from .io import MTKReader


class Training:
    def __init__(self, schema):
        schema_load, errors = TrainingSchema().load(schema)
        self.schema = schema_load
        self._gather_calculations()

    def _gather_calculations(self):
        self._calculations = []
        for calculation in self.schema['spec']:
            if calculation['type'] == 'mattoolkit':
                self._calculations.extend(self.download_mattoolkit_calculations(calculation['selector']))

    @property
    def calculations(self):
        return self._calculations

    def __iter__(self):
        return iter(self._calculations)

    def download_mattoolkit_calculations(self, selector):
        from mattoolkit.api import CalculationResourceList

        calculations = CalculationResourceList()
        calculations.get(params={'labels': selector['labels']})
        return [MTKReader(c.id) for c in calculations.items]

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
