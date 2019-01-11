import pytest

import python_jsonschema_objects as pjo
import json


@pytest.fixture
def base_schema():
    return {
        "title": "example",
        "type": "object",
        "properties": {"foobar": {"type": "boolean"}},
        "patternProperties": {
            "^foo.*": {"type": "string"},
            "^bar.*": {"type": "integer"},
        },
    }


def test_standard_properties_take_precedence(base_schema):
    """ foobar is a boolean, and it's a standard property,
    so we expect it will validate properly as a boolean,
    not using the patternProperty that matches it.
    """
    builder = pjo.ObjectBuilder(base_schema)
    ns = builder.build_classes()

    t = ns.Example(foobar=True)
    t.validate()

    with pytest.raises(pjo.ValidationError):
        # Try against the foo pattern
        x = ns.Example(foobar="hi")
        x.validate()


@pytest.mark.parametrize(
    "permit_addl,property,value,is_error",
    [
        (False, "foo", "hello", False),
        (False, "foobarro", "hello", False),
        (False, "foo", 24, True),
        (False, "barkeep", 24, False),
        (False, "barkeep", "John", True),
        (False, "extraprop", "John", True),
        (True, "extraprop", "John", False),
        # Test that the pattern props take precedence.
        # because these should validate against them, not the
        # additionalProperties that match
        (True, "foobar", True, False),
        (True, "foobar", "John", True),
        (True, "foobar", 24, True),
    ],
)
def test_pattern_properties_work(base_schema, permit_addl, property, value, is_error):

    base_schema["additionalProperties"] = permit_addl

    builder = pjo.ObjectBuilder(base_schema)
    ns = builder.build_classes()

    props = dict([(property, value)])

    if is_error:
        with pytest.raises(pjo.ValidationError):
            t = ns.Example(**props)
            t.validate()
    else:
        t = ns.Example(**props)
        t.validate()
