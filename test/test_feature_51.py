import pytest

import python_jsonschema_objects as pjo


def test_simple_array_anyOf():
    basicSchemaDefn = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Test",
        "properties": {"ExampleAnyOf": {"$ref": "#/definitions/exampleAnyOf"}},
        "required": ["ExampleAnyOf"],
        "type": "object",
        "definitions": {
            "exampleAnyOf": {
                # "type": "string", "format": "email"
                "anyOf": [
                    {"type": "string", "format": "email"},
                    {"type": "string", "maxlength": 0},
                ]
            }
        },
    }

    builder = pjo.ObjectBuilder(basicSchemaDefn)

    ns = builder.build_classes(any_of="use-first")
    ns.Test().from_json('{"ExampleAnyOf" : "test@example.com"}')

    with pytest.raises(pjo.ValidationError):
        # Because string maxlength 0 is not selected, as we are using the first validation in anyOf:
        ns.Test().from_json('{"ExampleAnyOf" : ""}')
        # Because this does not match the email format:
        ns.Test().from_json('{"ExampleAnyOf" : "not-an-email"}')

    # Does it also work when not deserializing?
    x = ns.Test()
    with pytest.raises(pjo.ValidationError):
        x.ExampleAnyOf = ""

    with pytest.raises(pjo.ValidationError):
        x.ExampleAnyOf = "not-an-email"

    x.ExampleAnyOf = "test@example.com"
    out = x.serialize()
    y = ns.Test.from_json(out)
    assert y.ExampleAnyOf == "test@example.com"


def test_nested_anyOf():
    basicSchemaDefn = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Test",
        "properties": {"ExampleAnyOf": {"$ref": "#/definitions/externalItem"}},
        "required": ["ExampleAnyOf"],
        "type": "object",
        "definitions": {
            "externalItem": {
                "type": "object",
                "properties": {
                    "something": {"type": "string"},
                    "exampleAnyOf": {
                        "anyOf": [
                            {"type": "string", "format": "email"},
                            {"type": "string", "maxlength": 0},
                        ]
                    },
                },
            }
        },
    }

    builder = pjo.ObjectBuilder(basicSchemaDefn)

    ns = builder.build_classes(any_of="use-first")
    ns.Test().from_json(
        '{"ExampleAnyOf" : {"something": "someone", "exampleAnyOf": "test@example.com"} }'
    )

    with pytest.raises(pjo.ValidationError):
        # Because this does not match the email format:
        ns.Test().from_json(
            '{"ExampleAnyOf" : {"something": "someone", "exampleAnyOf": "not-a-email-com"} }'
        )

    # Does it also work when not deserializing?
    x = ns.Test(ExampleAnyOf={"something": "somestring"})
    with pytest.raises(pjo.ValidationError):
        x.ExampleAnyOf.exampleAnyOf = ""

    with pytest.raises(pjo.ValidationError):
        x.ExampleAnyOf.exampleAnyOf = "not-an-email"

    x.ExampleAnyOf.exampleAnyOf = "test@example.com"
    out = x.serialize()
    y = ns.Test.from_json(out)
    assert y.ExampleAnyOf.exampleAnyOf == "test@example.com"


def test_simple_array_anyOf_withoutConfig():
    basicSchemaDefn = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Test",
        "properties": {"ExampleAnyOf": {"$ref": "#/definitions/exampleAnyOf"}},
        "required": ["ExampleAnyOf"],
        "type": "object",
        "definitions": {
            "exampleAnyOf": {
                # "type": "string", "format": "email"
                "anyOf": [
                    {"type": "string", "format": "email"},
                    {"type": "string", "maxlength": 0},
                ]
            }
        },
    }

    builder = pjo.ObjectBuilder(basicSchemaDefn)

    with pytest.raises(NotImplementedError):
        builder.build_classes()
