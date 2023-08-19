import json

import pytest

import python_jsonschema_objects as pjo

schema = """
{
    "title":"whatever",
    "properties": {
        "test": {"type": "number"}
    }
}
"""


@pytest.fixture
def schema_json():
    return json.loads(schema)


def test_literals_support_comparisons(schema_json):
    builder = pjo.ObjectBuilder(schema_json)
    ns = builder.build_classes()

    thing1 = ns.Whatever()
    thing2 = ns.Whatever()

    thing1.test = 10
    thing2.test = 12

    assert thing1.test < thing2.test
    assert thing1.test == thing1.test

    thing2.test = 10

    assert thing1.test <= thing2.test
    assert thing1.test == thing2.test
