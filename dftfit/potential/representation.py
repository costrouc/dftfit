""" A move to make Potentials as universal as possible


"""
import json
import hashlib

import yaml
import numpy as np
import pymatgen as pmg

from ..schema import PotentialSchema
from ..parameter import FloatParameter
from .. import db


class Potential:
    def __init__(self, schema):
        schema_load, errors = PotentialSchema().load(schema)
        self.schema = schema_load
        self._apply_constraints()
        self._collect_parameters()

    def _apply_constraints(self):
        for constraint, value in self.schema['spec'].get('constraint', {}).items():
            if constraint == 'charge_balance':
                composition = pmg.core.Composition(value)
                charges = self.schema['spec'].get('charge', {})
                if not {e.symbol for e in composition.keys()} <= charges.keys():
                    raise ValueError('charge ballance constrains requires all elements to be defined in charge')
                for charge_element in sorted(charges):
                    parameter = charges[charge_element]
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

        self._optimization_parameters = []
        self._optimization_parameter_indicies = []
        for i, p in enumerate(self._parameters):
            if not p.fixed:
                self._optimization_parameters.append(p)
                self._optimization_parameter_indicies.append(i)

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

    @classmethod
    def from_run_evaluation(cls, schema, initial_parameters, optimization_indicies, optimization_parameters, optimization_bounds):
        parameters = [value for value in initial_parameters]
        for i, value, bounds in zip(optimization_indicies, optimization_parameters, optimization_bounds):
            parameters[i] = {'initial': value, 'bounds': bounds}

        index = 0
        def _walk(value):  # Ordered traversal of dictionary
            nonlocal index
            if isinstance(value, dict):
                for key in sorted(value.keys()):
                    if isinstance(value[key], str) and value[key] == 'FloatParameter':
                        value[key] = parameters[index]
                        index += 1
                    else:
                        _walk(value[key])
            elif isinstance(value, (list)):
                for i, item in enumerate(value):
                    if isinstance(item, str) and item == 'FloatParameter':
                        value[i] = parameters[index]
                        index += 1
                    else:
                        _walk(item)
        _walk(schema)

        # Adding constraints
        for constraint, value in schema['spec'].get('constraint', {}).items():
            if constraint == 'charge_balance':
                composition = pmg.core.Composition(value)
                charges = schema['spec'].get('charge', {})
                if not {e.symbol for e in composition.keys()} <= charges.keys():
                    raise ValueError('charge ballance constrains requires all elements to be defined in charge')
                for charge_element in sorted(charges):
                    parameter = charges[charge_element]
                    if isinstance(parameter, (float, int)):
                        charge = 0
                        bounds = [0, 0]
                        for element, amount in composition.items():
                            if element.symbol != charge_element:
                                if isinstance(charges[element.symbol], dict):
                                    charge -= charges[element.symbol]['initial'] * amount
                                    bounds[0] -= charges[element.symbol].get('bounds', [0.0, 0.0])[1] * amount
                                    bounds[1] -= charges[element.symbol].get('bounds', [0.0, 0.0])[0] * amount
                                else:
                                    charge -= float(charges[element.symbol])
                        charges[charge_element] = {'initial': charge, 'bounds': bounds}
                        break
                else:
                    raise ValueError('unable to apply charge constraint no fixed values')
        return cls(schema)

    def md5hash(self):
        potential_str = json.dumps(self.as_dict(with_parameters=False), sort_keys=True)
        return hashlib.md5(potential_str.encode('utf-8')).hexdigest()

    @classmethod
    def from_best_optimized_for_potential_calulations(cls, potential, calculations, database_filename=None):
        # TODO: Notice that for now calculations are not considered for selection
        potential_str = json.dumps(potential.as_dict(with_parameters=False), sort_keys=True)
        potential_hash = hashlib.md5(potential_str.encode('utf-8')).hexdigest()
        optimized_potential = potential.copy()
        with db.DatabaseManager(database_filename or 'dftfit.db').transaction() as session:
            evaluation = session.query(db.Evaluation) \
                                .filter(db.Evaluation.potential_id == potential_hash) \
                                .order_by(db.Evaluation.score).first()
            parameters = json.loads(evaluation.parameters)
            optimized_potential.optimization_parameters = parameters
        return optimized_potential

    def as_dict(self, with_parameters=True):
        if with_parameters:
            schema_dump, errors = PotentialSchema().dump(self.schema)
            return schema_dump
        else:
            class CustomEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, FloatParameter):
                        return "FloatParameter"
                    else:
                        return super().default(obj)
            return json.loads(json.dumps(self.schema, cls=CustomEncoder))

    def write_file(self, filename):
        with open(filename, 'w') as f:
            f.write(str(self))

    def __copy__(self):
        return type(self)(self.as_dict())

    def copy(self):
        return self.__copy__()

    def __hash__(self):
        return hash(json.dumps(self.as_dict(with_parameters=False), sort_keys=True))

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

    @property
    def optimization_parameter_indicies(self):
        return np.array(self._optimization_parameter_indicies)

    @property
    def elements(self):
        """ Return a set of the elements that potential applies to
        """
        elements = set()
        for element in self.schema['spec'].get('charge', {}):
            elements.add(element)
        for parameter in self.schema['spec'].get('pair', {}).get('parameters', []):
            for element in parameter.get('elements', []):
                elements.add(element)
        return elements

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return json.dumps(self.as_dict(), sort_keys=True, indent=4)
