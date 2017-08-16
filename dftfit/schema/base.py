from marshmallow import Schema, ValidationError
from marshmallow.decorators import validates_schema


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
