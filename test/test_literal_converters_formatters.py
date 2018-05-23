import pytest  # noqa
import python_jsonschema_objects as pjo


def test_converters():
    schema = {
      'type': 'object',
      'title': 'BooleanConversion',
      'properties': {
          'answer': {'type': 'boolean'}
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
    print serialized


if __name__ == '__main__':
    test_converters()
    test_formatters()