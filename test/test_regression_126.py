import pytest
import python_jsonschema_objects as pjs
import collections


@pytest.fixture
def schema():
    return {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Test",
        "definitions": {
            "MyEnum1": {"type": "string", "enum": ["E_A", "E_B"]},
            "MyEnum2": {"type": "string", "enum": ["F_A", "F_B", "F_C", "F_D"]},
            "MyInt": {
                "default": "0",
                "type": "integer",
                "minimum": 0,
                "maximum": 4294967295,
            },
            "MyObj1": {
                "type": "object",
                "properties": {
                    "e1": {"$ref": "#/definitions/MyEnum1"},
                    "e2": {"$ref": "#/definitions/MyEnum2"},
                    "i1": {"$ref": "#/definitions/MyInt"},
                },
                "required": ["e1", "e2", "i1"],
            },
            "MyArray": {
                "type": "array",
                "items": {"$ref": "#/definitions/MyObj1"},
                "minItems": 0,
                "uniqueItems": True,
            },
            "MyMsg1": {
                "type": "object",
                "properties": {"a1": {"$ref": "#/definitions/MyArray"}},
            },
            "MyMsg2": {"type": "object", "properties": {"s1": {"type": "string"}}},
        },
        "type": "object",
        "oneOf": [{"$ref": "#/definitions/MyMsg1"}, {"$ref": "#/definitions/MyMsg2"}],
    }


def test_regression_126(schema):
    builder = pjs.ObjectBuilder(schema)
    ns = builder.build_classes(standardize_names=False)

    Obj1 = ns.MyObj1
    Array1 = ns.MyArray
    Msg1 = ns.MyMsg1
    o1 = Obj1(e1="E_A", e2="F_C", i1=2600)
    o2 = Obj1(e1="E_B", e2="F_D", i1=2500)
    objs = Array1([o1, o2])
    msg = Msg1(a1=objs)

    print(msg.serialize())
