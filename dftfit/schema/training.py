from marshmallow import fields, validate, ValidationError, validates, post_load
import numpy as np

from .base import BaseSchema
from .fields import PolyField


# Material Toolkit
class MTKSelectorSchema(BaseSchema):
    labels = fields.List(fields.String(), required=True)


class MTKTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('mattoolkit'))
    selector = fields.Nested(MTKSelectorSchema, required=True)


# Siesta
class SiestaSelectorSchema(BaseSchema):
    filename = fields.String(required=False)
    fileglob = fields.String(required=False)
    num_samples = fields.Integer(
        default=-1, validate=validate.Range(min=-1), required=False)
    strategy = fields.String(default='max-separation',
                             validate=validate.OneOf(['max-separation', 'all']),
                             required=False)

    @validates
    def validate_schema(self, data):
        if 'filename' not in data and 'fileglob' not in data:
            raise ValidationError('filename or fileglob must be specified')


class SiestaTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('Siesta'))
    selector = fields.Nested(SiestaSelectorSchema, required=True)


# reference ground state
class GroundStateTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('ground_state'))
    format = fields.String(required=True, validate=validate.OneOf(['cif', 'POSCAR']))
    data = fields.String(required=True)


# lattice_constants
class LatticeConstantTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('lattice_constants'))
    data = fields.List(fields.List(fields.Float(required=True), equal=3, required=True), validate=validate.Length(equal=2), required=True)

    @post_load
    def as_numpy_array(self, data):
        data['data'] = np.array(data['data']).reshape(2, 3)
        return data


# elastic_constants
class ElasticConstantTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('elastic_constants'))
    data = fields.List(fields.List(fields.Float(required=True), equal=6, required=True), validate=validate.Length(equal=6), required=True)

    @post_load
    def as_numpy_array(self, data):
        data['data'] = np.array(data['data']).reshape(6, 6)
        return data



# bulk_modulus
class BulkModulusTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('bulk_modulus'))
    data = fields.Float(required=True)


# shear_modulus
class ShearModulusTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('shear_modulus'))
    data = fields.Float(required=True)


# point defects
class PointDefectsTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('point_defects'))
    data = fields.Dict(required=True)


# displacement energies
class DisplacementEnergiesTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('displacement_energies'))
    data = fields.Dict(required=True)


# melting point
class MeltingPointEnergiesTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('melting_point'))
    data = fields.Float(required=True)


_TYPE_TO_SCHEMA = {
    'mattoolkit': MTKTrainingSetSchema,
    'Siesta': SiestaTrainingSetSchema,
    'ground_state': GroundStateTrainingSetSchema,
    'lattice_constants': LatticeConstantTrainingSetSchema,
    'elastic_constants': ElasticConstantTrainingSetSchema,
    'bulk_modulus': BulkModulusTrainingSetSchema,
    'shear_modulus': ShearModulusTrainingSetSchema,
    'point_defects': PointDefectsTrainingSetSchema,
    'displacement_energies': DisplacementEnergiesTrainingSetSchema,
    'melting_point': MeltingPointEnergiesTrainingSetSchema
}


def training_property_schema_serialization_disambiguation(base_object, obj):
    try:
        return _TYPE_TO_SCHEMA[obj.mode]()
    except KeyError:
        pass
    raise TypeError("Could not detect type did you specify a type?")


def trainging_property_schema_deserialization_disambiguation(object_dict, data):
    try:
        return _TYPE_TO_SCHEMA[object_dict['type']]()
    except KeyError:
        pass
    raise TypeError("Could not detect type did you specify a type?")


class TrainingSchema(BaseSchema):
    version = fields.String(required=True, validate=validate.Equal('v1'))
    kind = fields.String(required=True, validate=validate.Equal('Training'))
    spec = PolyField(
        serialization_schema_selector=training_property_schema_serialization_disambiguation,
        deserialization_schema_selector=trainging_property_schema_deserialization_disambiguation,
        many=True
    )
