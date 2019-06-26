import pytest

from jsonschema import validate
import python_jsonschema_objects as pjo
import json
import logging


@pytest.fixture
def nested_arrays():
    return {
        "title": "example",
        "properties": {
            "foo": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": [{"type": "number"}, {"type": "number"}],
                },
            }
        },
    }


@pytest.fixture
def instance():
    return {"foo": [[42, 44]]}


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


@pytest.fixture
def complex_schema():
    return json.loads(
        r'{"definitions": {"pnu_info": {"required": ["unit_name", "unit_type", "version", "system_time"], "type": "object", "properties": {"unit_type": {"enum": ["Other", "Backpack"], "type": "string"}, "unit_name": {"type": "string"}, "system_time": {"type": "string"}, "version": {"type": "string"}, "recording_state": {"type": "string"}}}, "error": {"additionalProperties": true, "required": ["message"], "type": "object", "properties": {"message": {"type": "string"}}}, "ptu_location": {"required": ["ptu_id", "latitude", "longitude"], "type": "object", "properties": {"latitude": {"type": "number"}, "ptu_id": {"type": "string"}, "longitude": {"type": "number"}, "orientation": {"minimum": 0, "type": "number", "description": "The orientation of this PTU (in degrees). 360 means *unknown*", "maximum": 360}}}, "geopath": {"items": {"required": ["lat", "lng"], "type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}}, "type": "array", "description": "A path described by an ordered\\nlist of lat/long coordinates\\n"}}, "required": ["status", "boundary", "members", "name"], "type": "object", "properties": {"status": {"enum": ["pending", "active", "completed"]}, "boundary": {"$ref": "#/definitions/geopath"}, "name": {"type": "string"}, "members": {"minItems": 1, "items": {"type": "string"}, "type": "array"}}, "title": "mission"}'
    )


def test_array_wrapper(complex_schema):
    instance = {
        "scenario_config": {"location_master": "MOCK"},
        "status": "pending",
        "boundary": [
            {"lat": 38.8821, "lng": -77.11461},
            {"lat": 38.882403, "lng": -77.107867},
            {"lat": 38.876293, "lng": -77.1083},
            {"lat": 38.880834, "lng": -77.115043},
        ],
        "name": "Test1",
        "members": ["Frobnaz", "MOCK"],
    }

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)
    builder = pjo.ObjectBuilder(complex_schema)
    ns = builder.build_classes()
    m = ns.Mission(**instance)
    m.validate()
