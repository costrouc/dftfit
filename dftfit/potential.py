""" A move to make Potentials as universal as possible


"""
import json

import yaml
import numpy as np

from .schema import PotentialSchema


class Potential:
    def __init__(self, schema):
        schema_load, errors = PotentialSchema().load(schema)
        self.schema = schema_load

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

    @property
    def parameters(self):
        """ Returns parameters for potentials as a list of float values

        """
        parameters = []
        if 'charge' in self.schema:
            for element in sorted(self.schema['charge'].keys()):
                parameters.append(self.schema['charge'][element])
        if 'pair' in self.schema:
            for parameter in self.schema['pair']['parameters']:
                parameters.extend(parameter['coefficients'])
        return np.array(parameters)

    @parameters.setter
    def parameters(self, parameters):
        """ Update potential with given parameters

        """
        # Parameters are ordered
        #   - alphabetically for dict
        #   - ordered for list
        index = 0
        if 'charge' in self.schema:
            for element in sorted(self.schema['charge'].keys()):
                self.schema['charge'][element] = parameters[index]
                index += 1
        if 'pair' in self.schema:
            for parameter in self.schema['pair']['parameters']:
                num_params = len(parameter['coefficients'])
                parameter['coefficients'] = parameters[index:index+num_params]
                index += num_params

        if index != len(parameters):
            raise ValueError('updating parameters does not match length of potential parameters')

    def __str__(self):
        return json.dumps(self.schema, sort_keys=True, indent=4)
