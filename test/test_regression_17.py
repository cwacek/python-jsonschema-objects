import pytest

import python_jsonschema_objects as pjo


@pytest.fixture
def test_class():
    schema = {
        "title": "Example",
        "properties": {
            "claimed_by": {
                "$id": "claimed",
                "type": ["string", "integer", "null"],
                "description": "Robots Only. The human agent that has claimed this robot.",
            }
        },
    }

    builder = pjo.ObjectBuilder(schema)
    ns = builder.build_classes()
    return ns


@pytest.mark.parametrize("value", ["Hi", 4, None])
def test_properties_can_have_multiple_types(test_class, value):
    test_class.Example(claimed_by=value)


@pytest.mark.parametrize("value", [2.4])
def test_multiply_typed_properties_still_validate(test_class, value):
    with pytest.raises(pjo.ValidationError):
        test_class.Example(claimed_by=value)
