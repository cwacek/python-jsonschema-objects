import pytest

import python_jsonschema_objects as pjo


@pytest.fixture
def base_schema():
    return {
        "title": "example",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "dictLike": {"additionalProperties": {"type": "integer"}, "type": "object"}
        },
    }


def test_wrong_exception_protocolbase_getitem(base_schema):
    """
    to declare a dict like object in json-schema, we are supposed
    to declare it as an object of additional properties.
    When trying to use it as dict, for instance testing if a key is inside
    the dictionary, methods like __contains__ in the ProtocolBase expect
    __getitem__ to raise a KeyError. getitem calls __getattr__ without any
    exception handling, which raises an AttributeError (necessary for proper
    behaviour of getattr, for instance).
    Solution found is to handle AttributeError in getitem and to raise KeyError
    """
    builder = pjo.ObjectBuilder(base_schema)
    ns = builder.build_classes()

    t = ns.Example(dictLike={"a": 0, "b": 1})
    t.validate()
    assert "a" in t.dictLike
    assert "c" not in t.dictLike
    assert getattr(t, "not_present", None) is None

    with pytest.raises(AttributeError):
        assert "a" not in t.notAnAttribute


if __name__ == "__main__":
    test_wrong_exception_protocolbase_getitem(base_schema())
