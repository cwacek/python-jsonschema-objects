import pytest

import python_jsonschema_objects as pjo


@pytest.fixture
def classes():
    schema = {
        "title": "Config",
        "type": "object",
        "additionalProperties": {"$ref": "#/definitions/Parameter"},
        "definitions": {
            "Parameter": {
                "$id": "Parameter",
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"oneOf": [{"type": "string"}, {"type": "number"}]},
                },
            }
        },
    }

    return pjo.ObjectBuilder(schema).build_classes()


def test_pjo_objects_can_be_used_as_property_keys(classes):
    container = classes.Config()
    obj1 = classes.Parameter(key="volume", value=11)
    obj2 = classes.Parameter(key="compression", value="on")

    container[obj1.key] = obj1
    container[obj2.key] = obj2

    assert container.volume.value == 11

    assert sorted(container.keys()) == sorted(str(k) for k in [obj1.key, obj2.key])
