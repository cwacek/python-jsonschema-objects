import jsonschema
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
            "oneOf": [
                {"$ref": "#/definitions/LocationIdentifier"},
                {"$ref": "#/definitions/LocationTyped"},
            ],
        },
        "LocationIdentifier": {
            "type": "integer",
            "minimum": 1,
        },
        "LocationTyped": {
            "additionalProperties": False,
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["Location"],
                    "default": "Location",
                }
            },
        },
        "UNIQUE_STRING": {
            "additionalProperties": False,
            "type": "string",
            "pattern": "^\\w[^:]*:.+$",
        },
    },
}


@pytest.fixture
def schema_json():
    return schema


def test_nested_oneof_with_different_types(schema_json):
    builder = pjo.ObjectBuilder(schema_json)
    ns = builder.build_classes()

    resolver = jsonschema.RefResolver.from_schema(schema_json)
    main_obj = schema_json["definitions"]["MainObject"]

    test1 = {"location": 12345}
    test2 = {"location": {"type": "Location"}}
    test3 = {"location": "unique:12"}
    jsonschema.validate(test1, main_obj, resolver=resolver)
    jsonschema.validate(test2, main_obj, resolver=resolver)
    jsonschema.validate(test3, main_obj, resolver=resolver)

    obj1 = ns.MainObject(**test1)
    obj2 = ns.MainObject(**test2)
    obj3 = ns.MainObject(**test3)

    assert obj1.location == 12345
    assert obj2.location.type == "Location"
    assert obj3.location == "unique:12"
