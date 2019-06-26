import pytest

import python_jsonschema_objects as pjs


def test_one_of_types():
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Example1",
        "type": "object",
        "properties": {"foo": {"oneOf": [{"type": "string"}, {"type": "null"}]}},
    }

    ns1 = pjs.ObjectBuilder(schema).build_classes()
    ns1.Example1(foo="bar")
    ns1.Example1(foo=None)
