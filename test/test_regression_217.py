import json
import pytest
import python_jsonschema_objects as pjo

schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "$id": "schema.json",
    "$ref": "#/definitions/test",
    "definitions": {
        "test": {
            "type": "object",
            "properties": {
                "name": {"$ref": "#/definitions/name"},
                "number": {"type": "number", "default": 10},
                "object": {"$ref": "#/definitions/object"},
            },
        },
        "name": {"type": "string", "default": "String"},
        "number": {"type": "number", "default": 10},
        "object": {"type": "object", "default": {}},
    },
}


@pytest.fixture
def schema_json():
    return schema


def test_reffed_defaults_work(schema_json):
    builder = pjo.ObjectBuilder(schema_json)
    ns = builder.build_classes()

    test = ns.Test()

    expected = {"name": "String", "number": 10, "object": {}}
    assert test.as_dict() == expected
