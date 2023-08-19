import json

import pytest

import python_jsonschema_objects as pjo

schema = """
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "Default Test",
  "type": "object",
    "properties": {
        "p1": {
            "type": ["integer", "null"],
            "default": 0
        },
        "p2": {
            "type": ["integer", "null"],
            "default": null
        },
        "p3": {
            "type": ["integer", "null"]
        }
    }
}
"""


@pytest.fixture
def schema_json():
    return json.loads(schema)


@pytest.fixture
def ns(schema_json):
    builder = pjo.ObjectBuilder(schema_json)
    ns = builder.build_classes()
    return ns


def test_defaults_serialize_for_nullable_types(ns):
    thing1 = ns.DefaultTest()

    assert thing1.as_dict() == {"p1": 0, "p2": None}


def test_nullable_types_are_still_nullable(ns):
    thing1 = ns.DefaultTest()

    thing1.p1 = 10
    thing1.validate()
    assert thing1.as_dict() == {"p1": 10, "p2": None}

    thing1.p1 = None
    thing1.validate()
    assert thing1.as_dict() == {"p1": 0, "p2": None}


def test_null_types_without_defaults_do_not_serialize(ns):
    thing1 = ns.DefaultTest()

    thing1.p3 = 10
    thing1.validate()
    thing1.p1 = None
    thing1.validate()

    assert thing1.as_dict() == {"p1": 0, "p2": None, "p3": 10}
