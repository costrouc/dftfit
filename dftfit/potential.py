""" A move to make Potentials as universal as possible


"""

from .schema import PotentialSchema
import json


class Potential:
    def __init__(self, schema):
        self.schema = PotentialSchema().load(schema)

    @property
    def parameters(self):
        """ Returns parameters for potentials as a list of float values

        """
        raise NotImplementedError()


    @parameters.setter
    def parameters(self, parameters):
        """ Update potential with given parameters

        """
        raise NotImplementedError()


    def __str__(self):
        return json.dumps(self.schema, sort_keys=True, indent=4)
