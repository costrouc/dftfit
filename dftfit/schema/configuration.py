from marshmallow import fields, validate, ValidationError

from .base import BaseSchema


class ConfigurationSchema(BaseSchema):
    version = fields.String(required=True, validate=validate.Equal('v1'))
    kind = fields.String(required=True, validate=validate.Equal('Configuration'))
    spec = fields.Dict()
