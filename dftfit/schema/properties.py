from marshmallow import fields, validate, ValidationError

from .base import BaseSchema


class PropertiesSchema(BaseSchema):
    version = fields.String(required=True, validate=validate.Equal('v1'))
    kind = fields.String(required=True, validate=validate.Equal('Properties'))
    spec = fields.Dict()
