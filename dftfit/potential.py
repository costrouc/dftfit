""" A move to make Potentials as universal as possible


"""
import json

import yaml

from .schema import PotentialSchema


class Potential:
    def __init__(self, schema):
        schema_load, errors = PotentialSchema().load(schema)
        self.schema = schema_load

    @property
    def parameters(self):
        """ Returns parameters for potentials as a list of float values

        """
        raise NotImplementedError()


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


    @parameters.setter
    def parameters(self, parameters):
        """ Update potential with given parameters

        """
        raise NotImplementedError()


    def __str__(self):
        return json.dumps(self.schema, sort_keys=True, indent=4)
