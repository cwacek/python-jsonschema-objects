import pytest
import json
import python_jsonschema_objects as pjo

import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)

schema = """
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "$id": "schema.json",
  "title":"Null Test",
  "type": "object",
  "$ref": "#/definitions/test",
  "definitions": {
    "test": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "default": "String"
        },
        "id": {
          "type": "null",
          "default": null
        }
      }
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
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)
    thing1 = ns.NullTest()

    serialized = thing1.as_dict()
    print(serialized)
    assert json.dumps(serialized) == """{"name": "String", "id": null}"""
    serialized = thing1.serialize()
    assert serialized == """{"name": "String", "id": null}"""
