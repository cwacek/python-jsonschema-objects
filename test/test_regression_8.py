import pytest

import python_jsonschema_objects as pjo


@pytest.fixture
def test_instance():
    schema = {
        "title": "Example",
        "properties": {
            "stringProp": {"type": "string"},
            "arrayProp": {"type": "array", "items": {"type": "string"}},
        },
    }

    builder = pjo.ObjectBuilder(schema)
    ns = builder.build_classes()
    instance = ns.Example(
        stringProp="This seems fine", arrayProp=["these", "are", "problematic"]
    )
    return instance


def test_string_properties_compare_to_strings(test_instance):
    test = test_instance.stringProp == "This seems fine"
    assert test


def test_arrays_of_strings_compare_to_strings(test_instance):
    test = test_instance.arrayProp == ["these", "are", "problematic"]
    assert test


def test_arrays_can_be_extended(test_instance):
    test_instance.arrayProp.extend(["...", "maybe", "not"])
    test = test_instance.arrayProp == [
        "these",
        "are",
        "problematic",
        "...",
        "maybe",
        "not",
    ]
    assert test


def test_array_elements_compare_to_types(test_instance):
    elem = test_instance.arrayProp[0]
    test = elem == "these"
    assert test


def test_repr_shows_property_values(test_instance):
    expected = "<Literal<str> these>"
    assert repr(test_instance.arrayProp[0]) == expected


def test_str_shows_just_strings(test_instance):
    test = str(test_instance.arrayProp[0])
    assert test == "these"
