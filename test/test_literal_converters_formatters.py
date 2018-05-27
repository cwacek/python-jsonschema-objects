import pytest  # noqa
import six
import python_jsonschema_objects as pjo
from python_jsonschema_objects.validators import converter_registry
from python_jsonschema_objects.validators import formatter_registry


@converter_registry.register(name='boolean')
def convert_boolean(param, value, _):
    if isinstance(value, six.string_types):
        vl = value.lower()
        if vl in ['true', 'yes', 'ok']:
            return True
        if vl in ['false', 'no', 'wrong']:
            return False
    return value


@formatter_registry.register(name='number')
def format_number(param, value, details):
    if 'format' in details:
        frmt = details['format']
        try:
            if '{' in frmt:
                return frmt.format(value)
            if '%' in frmt:
                return frmt % value
        except ValueError as er:
            pass
    return value

@converter_registry.register(name='enum')
def convert_enum(param, value, details):
    if isinstance(value, six.integer_types) and 'enum' in details:
        if (value-1) < len(details['enum']):
            return details['enum'][value-1]
    return value

def test_converters():
    schema = {
      'type': 'object',
      'title': 'BooleanConversion',
      'properties': {
          'answer': {'type': 'boolean'},
          'choice': {'enum': ['A', 'B', 'C'] }
        }
      }
    builder = pjo.ObjectBuilder(schema)
    klasses = builder.build_classes()
    bc = klasses.Booleanconversion()
    bc.answer = 'yes'
    assert bc.answer == True
    bc.answer = 'no'
    assert bc.answer == False
    bc.answer = True
    assert bc.answer == True
    bc.choice = 'A'
    assert bc.choice == 'A'
    bc.choice = 2
    assert bc.choice == 'B'
    with pytest.raises(pjo.ValidationError):
        bc.answer = "string not handled in boolean converter"


def test_formatters():
    schema = {
      'type': 'object',
      'title': 'FloatFormatter',
      'properties': {
          'new_format': {'type': 'number', 'format': '{:.2%}'},
          'old_format': {'type': 'number', 'format': '%.2f'}
        }
      }
    builder = pjo.ObjectBuilder(schema)
    klasses = builder.build_classes()
    ff = klasses.Floatformatter()
    ff.new_format = 0.236
    ff.old_format = 0.385
    assert str(ff.new_format) == '23.60%'
    assert str(ff.old_format) == '0.39'
    serialized = ff.serialize()
    assert serialized == '{"old_format": 0.385, "new_format": 0.236}'


if __name__ == '__main__':
    test_converters()
    test_formatters()