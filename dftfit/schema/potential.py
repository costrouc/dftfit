import sys

from marshmallow import fields, validate, ValidationError

from .base import BaseSchema
from ..data import element_symbols
from ..parameter import FloatParameter


class ParameterSchema(BaseSchema):
    initial = fields.Float(required=True)
    bounds = fields.List(fields.Float(), validate=validate.Length(equal=2), missing=(-sys.float_info.max, sys.float_info.max))


class FloatParameterField(fields.Field):
    def _deserialize(self, value, attr, data):
        try:
            value = float(value)
            return FloatParameter(value, fixed=True)
        except (ValueError, TypeError):
            schema_load, errors = ParameterSchema().load(value)
            return FloatParameter(**value)

    def _serialize(self, value, attr, data):
        if value.fixed and not value.computed:
            return float(value)
        else:
            return {'initial': float(value), 'bounds': value.bounds}

    def _validate(self, value):
        if value is None:
            return None
        try:
            super()._validate(float(value))
        except (ValueError, TypeError):
            schema_load, errors = ParameterSchema().load(value)
            if not (schema_load['bounds'][0] < schema_load['initial'] < schema_load['bounds'][1]):
                raise ValidationError('initial value must be between bounds', 'initial')
            super()._validate(schema_load['initial'])


class ConstraintSchema(BaseSchema):
    charge_balance = fields.String()
    equations = fields.List(fields.Dict())


ChargesSchema = type('ChargeSchema', (BaseSchema,), {element: FloatParameterField() for element in element_symbols})


class KspaceSchema(BaseSchema):
    KSPACE_TYPES = {'ewald', 'pppm'}

    type = fields.String(required=True, validate=validate.OneOf(KSPACE_TYPES))
    tollerance = FloatParameterField(required=True, validate=validate.Range(min=1e-16))


class ParametersSchema(BaseSchema):
    elements = fields.List(fields.String(validate=validate.OneOf(element_symbols)), required=True)
    coefficients = fields.List(FloatParameterField(allow_none=True))


class PairPotentialSchema(BaseSchema):
    PAIR_POTENTIALS = {
        'python-function',
        'lennard-jones',
        'buckingham',
        'zbl',
        'beck',
        'harmonic',
        'tersoff',
        'tersoff-2',
        'stillinger-weber',
        'gao-weber',
        'vashishta',
        'vashishta-mixing',
        'comb',
        'comb-3'
    }

    type = fields.String(required=True, validate=validate.OneOf(PAIR_POTENTIALS))
    cutoff = fields.List(FloatParameterField(validate=validate.Range(min=1e-6)), required=False)
    parameters = fields.Nested(ParametersSchema, required=True, many=True)
    samples = fields.Integer(required=False, validate=validate.Range(min=1))
    function = fields.String(required=False)


class PotentialSpecSchema(BaseSchema):
    constraint = fields.Nested(ConstraintSchema)
    charge = fields.Nested(ChargesSchema)
    kspace = fields.Nested(KspaceSchema)
    pair = fields.Nested(PairPotentialSchema, many=True)


class PotentialSchema(BaseSchema):
    version = fields.String(required=True, validate=validate.Equal('v1'))
    kind = fields.String(required=True, validate=validate.Equal('Potential'))
    spec = fields.Nested(PotentialSpecSchema)
