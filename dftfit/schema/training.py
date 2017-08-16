from marshmallow import fields, validate, ValidationError

from .base import BaseSchema
from .fields import PolyField


class MTKSelectorSchema(BaseSchema):
    labels = fields.List(fields.String(), required=True)


class MTKTrainingSetSchema(BaseSchema):
    type = fields.String(required=True, validate=validate.Equal('mattoolkit'))
    selector = fields.Nested(MTKSelectorSchema, required=True)


def training_property_schema_serialization_disambiguation(base_object, obj):
    type_to_schema = {
        'mattoolkit': MTKTrainingSetSchema,
    }
    try:
        return type_to_schema[obj.mode]()
    except KeyError:
        pass
    raise TypeError("Could not detect type did you specify a type?")


def trainging_property_schema_deserialization_disambiguation(object_dict, data):
    type_to_schema = {
        'mattoolkit': MTKTrainingSetSchema,
    }
    try:
        return type_to_schema[object_dict['type']]()
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
