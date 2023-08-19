import pytest

import python_jsonschema_objects as pjo


def test_simple_array_oneOf():
    basicSchemaDefn = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Test",
        "properties": {
            "SimpleArrayOfNumberOrString": {"$ref": "#/definitions/simparray"}
        },
        "required": ["SimpleArrayOfNumberOrString"],
        "type": "object",
        "definitions": {
            "simparray": {
                "oneOf": [
                    {"type": "array", "items": {"type": "number"}},
                    {"type": "array", "items": {"type": "string"}},
                ]
            }
        },
    }

    builder = pjo.ObjectBuilder(basicSchemaDefn)

    ns = builder.build_classes()
    ns.Test().from_json('{"SimpleArrayOfNumberOrString" : [0, 1]}')
    ns.Test().from_json('{"SimpleArrayOfNumberOrString" : ["Hi", "There"]}')

    with pytest.raises(pjo.ValidationError):
        ns.Test().from_json('{"SimpleArrayOfNumberOrString" : ["Hi", 0]}')
