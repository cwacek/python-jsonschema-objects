import pytest

import python_jsonschema_objects as pjo
import json


@pytest.fixture
def base_schema():
    return {
        'title': 'example',
        'type': 'object',
        "additionalProperties": False, 
        "properties": {
          "dictLike": {
            "additionalProperties": {
              "type": "integer"
            }, 
            "type": "object"
          }
        }
    }


def test_wrong_exception_protocolbase_getattr(base_schema):
    """
    to declare a dict like object in json-schema, we are supposed
    to declare it as an object of additional properties.
    When trying to use it as dict, for instance testing if a key is inside
    the dictionary, methods like __contains__ in the ProtocolBase expect
    getattr to raise a KeyError. For additional properties, the error raised
    is AttributeError, breaking the expected behaviour.
    """
    builder = pjo.ObjectBuilder(base_schema)
    ns = builder.build_classes()

    t = ns.Example(dictLike={'a': 0,'b': 1})
    t.validate()
    assert 'a' in t.dictLike
    assert not 'c' in t.dictLike

if __name__ == '__main__':
    test_wrong_exception_protocolbase_getattr(base_schema()) 
