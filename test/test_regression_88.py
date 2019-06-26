import pytest
import json

import python_jsonschema_objects as pjs


def test_nested_arrays_work_fine():
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Example1",
        "type": "object",
        "properties": {
            "name": {
                "type": "array",
                "items": {"type": "object", "properties": {"name": {"type": "string"}}},
            }
        },
    }

    ns1 = pjs.ObjectBuilder(schema).build_classes()
    j1 = ns1.Example1.from_json(
        json.dumps({"name": [{"value": "foo"}, {"value": "bar"}]})
    )
    assert j1.name[0].value == "foo"
    assert j1.name[1].value == "bar"


def test_top_level_arrays_are_converted_to_objects_properly():
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Example2",
        "type": "array",
        "items": {"type": "object", "properties": {"name": {"type": "string"}}},
    }

    ns2 = pjs.ObjectBuilder(schema).build_classes()
    j2 = ns2.Example2.from_json(json.dumps([{"name": "foo"}, {"name": "bar"}]))
    assert not isinstance(j2[0], dict)  # Out[173]: {'name': 'foo'}
    assert j2[0].name == "foo"
    assert j2[1].name == "bar"
