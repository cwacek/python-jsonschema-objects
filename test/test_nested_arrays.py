
import pytest

from jsonschema import validate
import python_jsonschema_objects as pjo
import json
import logging


@pytest.fixture
def nested_arrays():
    return {
        "title": 'example',
        "properties": {
            "foo": {
                "type": "array",
                "items": {
                        "type": "array",
                        'items': [
                            {'type': 'number'},
                            {'type': 'number'}
                        ]
                }
            }
        }

    }

@pytest.fixture
def instance():
    return {'foo': [[42, 44]]}


def test_validates(nested_arrays, instance):
    validate(instance, nested_arrays)


def test_nested_array_regression(nested_arrays, instance):
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)
    builder = pjo.ObjectBuilder(nested_arrays)
    ns = builder.build_classes()

    q = ns.Example.from_json(json.dumps(instance))

    assert q.serialize() == '{"foo": [[42, 44]]}'

    assert q.as_dict() == {"foo": [[42, 44]]}
