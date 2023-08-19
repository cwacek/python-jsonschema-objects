import jsonschema
import pytest

import python_jsonschema_objects as pjo

schema = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "title": "myschema",
    "type": "object",
    "definitions": {
        "RefObject": {
            "title": "Ref Object",
            "properties": {"location": {"$ref": "#/definitions/Location"}},
        },
        "MapObject": {
            "title": "Map Object",
            "additionalProperties": {"$ref": "#/definitions/Location"},
        },
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
            "pattern": r"^\w[^:]*:.+$",
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


def test_nested_oneof_with_different_types_by_reference(schema_json):
    builder = pjo.ObjectBuilder(schema_json)
    ns = builder.build_classes()

    resolver = jsonschema.RefResolver.from_schema(schema_json)
    ref_obj = schema_json["definitions"]["RefObject"]

    test1 = {"location": 12345}
    test2 = {"location": {"type": "Location"}}
    jsonschema.validate(test1, ref_obj, resolver=resolver)
    jsonschema.validate(test2, ref_obj, resolver=resolver)

    obj1 = ns.RefObject(**test1)
    obj2 = ns.RefObject(**test2)

    assert obj1.location == 12345
    assert obj2.location.type == "Location"


def test_nested_oneof_with_different_types_in_additional_properties(schema_json):
    builder = pjo.ObjectBuilder(schema_json)
    ns = builder.build_classes()

    resolver = jsonschema.RefResolver.from_schema(schema_json)
    map_obj = schema_json["definitions"]["MapObject"]

    x_prop_name = "location-id"

    test1 = {x_prop_name: 12345}
    test2 = {x_prop_name: {"type": "Location"}}
    jsonschema.validate(test1, map_obj, resolver=resolver)
    jsonschema.validate(test2, map_obj, resolver=resolver)

    obj1 = ns.MapObject(**test1)
    obj2 = ns.MapObject(**test2)

    assert obj1[x_prop_name] == 12345
    assert obj2[x_prop_name].type == "Location"
