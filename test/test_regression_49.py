import pytest

from jsonschema import validate
import python_jsonschema_objects as pjo
import json


@pytest.fixture
def bad_schema_49():
    return {
        "title": "example",
        "type": "array",
        "items": {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {"a": {"type": "string"}},
                    "required": ["a"],
                },
                {
                    "type": "object",
                    "properties": {"b": {"type": "string"}},
                    "required": ["b"],
                },
            ]
        },
    }


@pytest.fixture
def instance():
    return [{"a": ""}, {"b": ""}]


def test_is_valid_jsonschema(bad_schema_49, instance):
    validate(instance, bad_schema_49)


def test_regression_49(bad_schema_49, instance):
    builder = pjo.ObjectBuilder(bad_schema_49)
    ns = builder.build_classes()

    ns.Example.from_json(json.dumps(instance))
