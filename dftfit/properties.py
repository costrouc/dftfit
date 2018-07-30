""" Handles collection of measured material properties

"""

from .schema import PropertiesSchema


class MaterialProperties:
    def __init__(self, schema):
        schema_load, errors = PropertiesSchema().load(schema)
        self.schema = schema_load
