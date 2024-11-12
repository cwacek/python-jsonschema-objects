import logging

import pytest

import python_jsonschema_objects as pjs
import referencing

SCHEMA_A = {
    "$id": "schema-a",
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Schema A",
    "definitions": {
        "myint": {"type": "integer", "minimum": 42},
        "myintarray": {
            "type": "array",
            "items": {
                "$ref": "#/definitions/myint",  # using 'schema-a#/definitions/myint' would work
            },
        },
        "myintref": {
            "$ref": "#/definitions/myint",  # using 'schema-a#/definitions/myint' would work
        },
    },
    "type": "object",
    "properties": {
        "theint": {
            "$ref": "#/definitions/myint",  # using 'schema-a#/definitions/myint' would work
        },
    },
}


def test_referenced_schema_works_indirectly():
    registry = referencing.Registry().with_resources(
        [
            ("schema-a", referencing.Resource.from_contents(SCHEMA_A)),
        ]
    )

    # works fine
    builder_a = pjs.ObjectBuilder(SCHEMA_A, registry=registry)
    namespace_a = builder_a.build_classes(named_only=False)

    b = namespace_a.SchemaA()
    b.obja = {"theint": 42}
    b.theintarray = [42, 43, 44]
    b.theintref = 42
    print(b.for_json())


@pytest.mark.parametrize(
    "ref",
    [
        "schema-a#/definitions/myint",
        "schema-a#/definitions/myintref",  # This is an interesting variation, because this ref is itself a ref.
    ],
)
def test_referenced_schema_works_directly(ref):
    registry = referencing.Registry().with_resources(
        [
            ("schema-a", referencing.Resource.from_contents(SCHEMA_A)),
        ]
    )

    # WE make a dumb schema that references this
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "$id": "test",
        "title": "Test",
        "type": "object",
        "properties": {"name": {"$ref": ref}},
    }

    # works fine
    builder_a = pjs.ObjectBuilder(schema, registry=registry)
    namespace_a = builder_a.build_classes(named_only=False)

    b = namespace_a.Test()
    b.name = 42
    print(b.for_json())


def test_you_do_actually_need_a_reference():
    logging.basicConfig(level=logging.DEBUG)

    registry = referencing.Registry().with_resources(
        [
            ("schema-a", referencing.Resource.from_contents(SCHEMA_A)),
        ]
    )

    # WE make a dumb schema that references
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "$id": "test",
        "title": "Test",
        "type": "object",
        "properties": {
            "name": {
                "$ref": "#/definitions/myint",
            }
        },
    }

    # works fine
    builder_a = pjs.ObjectBuilder(schema, registry=registry)
    with pytest.raises(Exception):
        # WE would expect this to fail because this isn't actually
        # a good reference. Our schema doesn't have a definitions block,
        # so schema-a should be a required URI
        builder_a.build_classes(named_only=False)


def test_regression_292():
    SCHEMA_B = {
        "$id": "schema-b",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Schema B",
        "type": "object",
        "definitions": {
            "myintref": {
                "$ref": "schema-a#/definitions/myint",
            },
        },
        "properties": {
            # all three properties cause the failure
            "obja": {
                "$ref": "schema-a",
            },
            "theintarray": {
                "$ref": "schema-a#/definitions/myintarray",
            },
            "thedirectintref": {
                "$ref": "schema-a#/definitions/myint",
            },
            "theintref": {
                "$ref": "#/definitions/myintref",
            },
        },
    }

    registry = referencing.Registry().with_resources(
        [
            ("schema-a", referencing.Resource.from_contents(SCHEMA_A)),
        ]
    )

    # fails
    builder_b = pjs.ObjectBuilder(SCHEMA_B, registry=registry)
    namespace_b = builder_b.build_classes(
        named_only=False
    )  # referencing.exceptions.PointerToNowhere: '/definitions/myint' does not exist within SCHEMA_B

    b = namespace_b.SchemaB()
    b.obja = {"theint": 42}
    b.theintarray = [42, 43, 44]
    b.theintref = 42
    print(b.for_json())
