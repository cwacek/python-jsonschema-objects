import jsonschema.exceptions
import pytest  # noqa
import referencing
import referencing.exceptions
import referencing.jsonschema

import python_jsonschema_objects
import python_jsonschema_objects as pjo


def test_custom_spec_validator(markdown_examples):
    # This schema shouldn't be valid under DRAFT-03
    schema = {
        "$schema": "http://json-schema.org/draft-03/schema",
        "title": "other",
        "type": "any",  # this wasn't valid starting in 04
    }
    pjo.ObjectBuilder(
        schema,
        resolved=markdown_examples,
    )

    with pytest.raises(jsonschema.exceptions.ValidationError):
        pjo.ObjectBuilder(
            schema,
            specification_uri="http://json-schema.org/draft-04/schema",
            resolved=markdown_examples,
        )


def test_non_default_resolver_finds_refs():
    registry = referencing.Registry()

    remote_schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "type": "number",
    }
    registry = registry.with_resource(
        "https://example.org/schema/example",
        referencing.Resource.from_contents(remote_schema),
    )

    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "other",
        "type": "object",
        "properties": {
            "local": {"type": "string"},
            "remote": {"$ref": "https://example.org/schema/example"},
        },
    }

    builder = pjo.ObjectBuilder(
        schema,
        registry=registry,
    )
    ns = builder.build_classes()

    thing = ns.Other(local="foo", remote=1)
    with pytest.raises(python_jsonschema_objects.ValidationError):
        thing = ns.Other(local="foo", remote="NaN")
