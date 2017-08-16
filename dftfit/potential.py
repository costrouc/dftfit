""" A move to make Potentials as universal as possible


"""
import json

import yaml
import numpy as np
from pymatgen.core import Composition

from .schema import PotentialSchema
from .parameter import FloatParameter


class Potential:
    def __init__(self, schema):
        schema_load, errors = PotentialSchema().load(schema)
        self.schema = schema_load
        self._apply_constraints()
        self._collect_parameters()

    def _apply_constraints(self):
        for constraint, value in self.schema['spec'].get('constraint', {}).items():
            if constraint == 'charge_balance':
                composition = Composition(value)
                charges = self.schema['spec'].get('charge', {})
                if not {e.symbol for e in composition.keys()} <= charges.keys():
                    raise ValueError('charge ballance constrains requires all elements to be defined in charge')
                for charge_element, parameter in charges.items():
                    if isinstance(parameter, FloatParameter) and parameter.computed == None:
                        break
                else:
                    if abs(sum(float(charges[element.symbol]) * amount for element, amount in composition.items())) > 1e-8:
                        raise ValueError('no parameters to apply charge constraint and charge does ballance')
                    continue
                parameter.computed = lambda: -sum(float(charges[element.symbol]) * amount for element, amount in composition.items() if element.symbol != charge_element)

    def _collect_parameters(self):
        self._parameters = []

        def _walk(value):
            if isinstance(value, dict):
                for key in value:
                    _walk(value[key])
            elif isinstance(value, (tuple, list)):
                for item in value:
                    _walk(item)
            elif isinstance(value, FloatParameter) and value.computed == None:
                self._parameters.append(value)
        _walk(self.schema)

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
        return np.array([float(parameter) for parameter in self._parameters])

    @parameters.setter
    def parameters(self, parameters):
        """ Update potential with given parameters

        """
        if len(parameters) != len(self._parameters):
            raise ValueError('updating parameters does not match length of potential parameters')

        for parameter, update_parameter in zip(self._parameters, parameters):
            parameter.current = update_parameter

    def __str__(self):
        return json.dumps(self.schema, sort_keys=True, indent=4)
