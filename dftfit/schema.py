import sys

from marshmallow import Schema, fields, validate, ValidationError, pre_load
from marshmallow.decorators import validates_schema

from .data import element_symbols


class BaseSchema(Schema):
    def __init__(self, strict=True, **kwargs):
        super(Schema, self).__init__(strict=strict, **kwargs)

    @validates_schema(pass_original=True, pass_many=False, skip_on_field_errors=True)
    def check_unknown_fields(self, data, original_data):
        def check_unknown(original_data_single):
            dump_only_keys = {key for key in self.fields if self.fields[key].dump_only}

            unknown_dump = set(dump_only_keys) & set(original_data_single)
            unknown_invalid = set(original_data_single) - set(self.fields.keys())
            unknown = unknown_dump | unknown_invalid
            if unknown:
                raise ValidationError('Unknown field', unknown)

        if isinstance(original_data, list):
            for original_data_single in original_data:
                check_unknown(original_data_single)
        else:
            check_unknown(original_data)


class Parameter:
    """ Float with tracking. initial value and bounds.

    """
    def __init__(self, initial, bounds=(-sys.float_info.max, sys.float_info.max), computed=None):
        self.initial = float(initial)
        self.current = float(initial)
        self.bounds = [float(_) for _ in bounds]
        self.computed = computed

    def __float__(self):
        if self.computed is None:
            return self.current
        return self.computed()

    def __str__(self):
        return str(self.current)


class ParameterSchema(BaseSchema):
    initial = fields.Float(required=True)
    bounds = fields.List(fields.Float(), validate=validate.Length(equal=2), missing=(-sys.float_info.max, sys.float_info.max))


class FloatOrParameter(fields.Field):
    def _deserialize(self, value, attr, data):
        try:
            return float(value)
        except (ValueError, TypeError):
            schema_load, errors = ParameterSchema().load(value)
            return Parameter(**value)

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


ChargesSchema = type('ChargeSchema', (BaseSchema,), {element: FloatOrParameter() for element in element_symbols})


class KspaceSchema(BaseSchema):
    KSPACE_TYPES = {'ewald', 'pppm'}

    type = fields.String(required=True, validate=validate.OneOf(KSPACE_TYPES))
    tollerance = FloatOrParameter(required=True, validate=validate.Range(min=1e-16))


class ParametersSchema(BaseSchema):
    elements = fields.List(fields.String(validate=validate.OneOf(element_symbols)), required=True)
    coefficients = fields.List(FloatOrParameter())


class PairPotentialSchema(BaseSchema):
    PAIR_POTENTIALS = {'buckingham'}

    type = fields.String(required=True, validate=validate.OneOf(PAIR_POTENTIALS))
    cutoff = FloatOrParameter(required=True, validate=validate.Range(min=1e-6))
    parameters = fields.Nested(ParametersSchema, required=True, many=True)


class PotentialSpecSchema(BaseSchema):
    constraint = fields.Nested(ConstraintSchema)
    charge = fields.Nested(ChargesSchema)
    kspace = fields.Nested(KspaceSchema)
    pair = fields.Nested(PairPotentialSchema)


class PotentialSchema(BaseSchema):
    version = fields.String(required=True, validate=validate.Equal('v1'))
    kind = fields.String(required=True, validate=validate.Equal('Potential'))
    spec = fields.Nested(PotentialSpecSchema)
