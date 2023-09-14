import pytest

import python_jsonschema_objects as pjo

schema = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "title": "myschema",
    "type": "object",
    "definitions": {
        "MainObject": {
            "title": "Main Object",
            "additionalProperties": False,
            "type": "object",
            "properties": {
                "location": {
                    "title": "location",
                    "type": ["object", "string"],
                    "oneOf": [
                        {"$ref": "#/definitions/UNIQUE_STRING"},
                        {"$ref": "#/definitions/Location"},
                    ],
                }
            },
        },
        "Location": {
            "title": "Location",
            "description": "A Location represents a span on a specific sequence.",
            "type": "object",
            "oneOf": [
                {"$ref": "#/definitions/Location1"},
                {"$ref": "#/definitions/Location2"},
            ],
            "discriminator": {"propertyName": "type"},
        },
        "Location1": {
            "additionalProperties": False,
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["Location1"],
                    "default": "Location1",
                }
            },
        },
        "Location2": {
            "additionalProperties": False,
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["Location2"],
                    "default": "Location2",
                }
            },
        },
        "UNIQUE_STRING": {
            "additionalProperties": False,
            "type": "string",
            "pattern": r"^\w[^:]*:.+$",
        },
    },
}


@pytest.fixture
def schema_json():
    return schema


def test_nested_oneofs_still_work(schema_json):
    builder = pjo.ObjectBuilder(schema_json)
    ns = builder.build_classes()

    obj1 = ns.MainObject(**{"location": {"type": "Location1"}})
    obj2 = ns.MainObject(**{"location": {"type": "Location2"}})
    obj3 = ns.MainObject(**{"location": "unique:12"})

    assert obj1.location.type == "Location1"
    assert obj2.location.type == "Location2"
    assert obj3.location == "unique:12"
