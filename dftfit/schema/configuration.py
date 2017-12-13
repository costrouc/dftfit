from marshmallow import fields, validate, ValidationError

from .base import BaseSchema


class KeyValueField(fields.Field):
    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        if not isinstance(value, dict):
            self.fail('invalid must be key value dict')
        for key in value:
            if not isinstance(key, str) or not isinstance(value[key], str):
                self.fail('key value pairs must be strings')
        return value

    def _serialize(self, value, attr, data):
        return value


class MetadataSchema(BaseSchema):
    name = fields.String()
    labels = KeyValueField()


class ConfigurationSchema(BaseSchema):
    version = fields.String(required=True, validate=validate.Equal('v1'))
    kind = fields.String(required=True, validate=validate.Equal('Configuration'))
    metadata = fields.Nested(MetadataSchema)
    spec = fields.Dict()
