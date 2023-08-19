import json

import pytest

import python_jsonschema_objects as pjo

schema = """
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "$id": "roundtrip.json",
  "type": "object",
  "properties":
  {
    "container": {"$ref": "#/definitions/config"}
  },
  "definitions": {
    "config": {
      "properties":{
        "something": {
          "allOf": [
            {
              "$ref": "#/definitions/params"
            },
            {
              "properties":{
                "parameters": {
                  "oneOf": [
                    {
                      "$ref": "#/definitions/parametersA"
                    },
                    {
                      "$ref": "#/definitions/parametersB"
                    }
                  ]
                }
              },
              "required": ["parameters"]
            }
          ]
        }
      }
    },
    "params": {
      "type": "object",
      "properties": {
        "param1": {
          "type": "string"
        },
        "param2": {
          "type": "string"
        }
      },
      "required": [
        "param1",
        "param2"
      ]
    },
    "parametersA": {
      "properties": {
        "name": {
          "type": "string"
        },
        "value": {
          "type": "string"
        }
      },
      "required": [
        "name",
        "value"
      ]
    },
    "parametersB": {
      "properties": {
        "something": {
          "type": "string"
        },
        "another": {
          "type": "string"
        }
      },
      "required": [
        "something",
        "another"
      ]
    }
  }
}
"""


@pytest.fixture
def schema_json():
    return json.loads(schema)


def test_roundtrip_oneof_serializer(schema_json):
    builder = pjo.ObjectBuilder(schema_json)
    namespace = builder.build_classes()

    data_config = """
    {
    "something": "a name",
    "another": "a value"
    }
    """
    paramsTypeB = namespace.Parametersb().from_json(data_config)
    somethingInstance = namespace.Something(param1="toto", param2="tata")
    somethingInstance.parameters = paramsTypeB

    json_object = somethingInstance.serialize()
    print(json_object)

    aNewsomething = namespace.Something.from_json(json_object)

    json_object2 = aNewsomething.serialize()
    assert json_object == json_object2
