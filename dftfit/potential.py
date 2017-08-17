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
                    if isinstance(parameter, FloatParameter) and not parameter.fixed:
                        break
                else:
                    if abs(sum(float(charges[element.symbol]) * amount for element, amount in composition.items())) > 1e-8:
                        raise ValueError('no parameters to apply charge constraint and charge does ballance')
                    continue
                parameter.computed = lambda: -sum(float(charges[element.symbol]) * amount for element, amount in composition.items() if element.symbol != charge_element)

    def _collect_parameters(self):
        self._parameters = []

        def _walk(value): # Ordered traversal of dictionary
            if isinstance(value, dict):
                for key in sorted(value.keys()):
                    _walk(value[key])
            elif isinstance(value, (tuple, list)):
                for item in value:
                    _walk(item)
            elif isinstance(value, FloatParameter):
                self._parameters.append(value)
        _walk(self.schema)

        self._optimization_parameters = [p for p in self._parameters if not p.fixed]

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

    def as_dict(self):
        schema_dump, errors = PotentialSchema().dump(self.schema)
        return schema_dump

    def __copy__(self):
        return type(self)(self.as_dict())

    def copy(self):
        return self.__copy__()

    def __hash__(self):
        class CustomEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, FloatParameter):
                    return "FloatParameter"
                else:
                    return super().default(obj)
        return hash(json.dumps(self.schema, sort_keys=True, cls=CustomEncoder))

    def __eq__(self, other):
        return hash(self) == hash(other) and np.all(np.isclose(self.parameters, other.parameters, rtol=1e-16))

    @property
    def parameters(self):
        """ Returns parameters for potentials as a list of float values

        """
        return np.array([float(parameter) for parameter in self._parameters])

    @property
    def optimization_parameters(self):
        return np.array([float(parameter) for parameter in self._optimization_parameters])

    @optimization_parameters.setter
    def optimization_parameters(self, parameters):
        """ Update potential with given parameters

        """
        if len(parameters) != len(self._optimization_parameters):
            raise ValueError('updating parameters does not match length of potential parameters')

        for parameter, update_parameter in zip(self._optimization_parameters, parameters):
            parameter.current = float(update_parameter)

    @property
    def optimization_bounds(self):
        return np.array([parameter.bounds for parameter in self._optimization_parameters])

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return json.dumps(self.as_dict(), sort_keys=True, indent=4)
