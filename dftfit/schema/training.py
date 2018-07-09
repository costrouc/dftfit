from marshmallow import fields, validate, ValidationError

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
    filename = fields.String(required=True)
    num_samples = fields.Integer(
        default=-1, validate=validate.Range(min=-1), required=False)
    strategy = fields.String(default='max-separation',
                             validate=validate.OneOf(['max-separation', 'all']),
                             required=False)


class SiestaTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('Siesta'))
    selector = fields.Nested(SiestaSelectorSchema, required=True)


_TYPE_TO_SCHEMA = {
    'mattoolkit': MTKTrainingSetSchema,
    'Siesta': SiestaTrainingSetSchema,
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
