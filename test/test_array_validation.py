import pytest

import python_jsonschema_objects as pjo


@pytest.fixture
def arrayClass():
    schema = {
        "title": "ArrayVal",
        "type": "object",
        "properties": {
            "min": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
                "minItems": 1,
            },
            "max": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
                "maxItems": 1,
            },
            "both": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
                "maxItems": 2,
                "minItems": 1,
            },
            "unique": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
                "uniqueItems": True,
            },
            "reffed": {
                "type": "array",
                "items": {"$ref": "#/definitions/myref"},
                "minItems": 1,
            },
        },
        "definitions": {"myref": {"type": "string"}},
    }

    ns = pjo.ObjectBuilder(schema).build_classes()
    return ns["Arrayval"](min=["1"], both=["1"])


def test_validators_work_with_reference(arrayClass):
    arrayClass.reffed = ["foo"]

    with pytest.raises(pjo.ValidationError):
        arrayClass.reffed = []


def test_array_length_validates(markdown_examples):

    builder = pjo.ObjectBuilder(
        markdown_examples["Example Schema"], resolved=markdown_examples
    )
    ns = builder.build_classes()

    with pytest.raises(pjo.ValidationError):
        ns.ExampleSchema(
            firstName="Fred",
            lastName="Huckstable",
            dogs=["Fido", "Spot", "Jasper", "Lady", "Tramp"],
        )


def test_minitems(arrayClass):

    arrayClass.min = ["1"]
    arrayClass.min.append("2")

    with pytest.raises(pjo.ValidationError):
        arrayClass.min = []


def test_maxitems(arrayClass):

    arrayClass.max = []
    arrayClass.max.append("2")

    assert arrayClass.max == ["2"]

    with pytest.raises(pjo.ValidationError):
        arrayClass.max.append("3")
        # You have to explicitly validate with append
        arrayClass.validate()

    with pytest.raises(pjo.ValidationError):
        arrayClass.max = ["45", "42"]


def test_unique(arrayClass):

    arrayClass.unique = ["hi", "there"]
    with pytest.raises(pjo.ValidationError):
        arrayClass.unique.append("hi")
        # You have to explicitly validate with append
        arrayClass.validate()

    with pytest.raises(pjo.ValidationError):
        arrayClass.unique = ["Fred", "Fred"]
