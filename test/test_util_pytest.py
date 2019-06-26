import pytest

from python_jsonschema_objects.validators import ValidationError
from python_jsonschema_objects.wrapper_types import ArrayWrapper


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"item_constraint": {"type": "string"}},
        {"item_constraint": [{"type": "string"}, {"type": "string"}]},
    ],
)
def test_ArrayValidator_initializer(kwargs):
    assert ArrayWrapper.create("hello", **kwargs)


def test_ArrayValidator_throws_error_if_not_classes_or_dicts():
    with pytest.raises(TypeError):
        ArrayWrapper.create("hello", item_constraint=["winner"])


def test_validate_basic_array_types():
    validator = ArrayWrapper.create("test", item_constraint={"type": "number"})

    instance = validator([1, 2, 3, 4])

    instance.validate()

    instance = validator([1, 2, "Hello"])
    with pytest.raises(ValidationError):
        instance.validate()


def test_validate_basic_tuple__types():
    validator = ArrayWrapper.create(
        "test", item_constraint=[{"type": "number"}, {"type": "number"}]
    )

    instance = validator([1, 2, 3, 4])

    instance.validate()

    instance = validator([1, "Hello"])
    with pytest.raises(ValidationError):
        instance.validate()


def test_validate_arrays_with_object_types(Person):
    validator = ArrayWrapper.create("test", item_constraint=Person)

    instance = validator([{"firstName": "winner", "lastName": "Smith"}])
    instance.validate()

    instance = validator(
        [{"firstName": "winner", "lastName": "Dinosaur"}, {"firstName": "BadMan"}]
    )
    with pytest.raises(ValidationError):
        instance.validate()


def test_validate_arrays_with_mixed_types(Person):

    validator = ArrayWrapper.create(
        "test", item_constraint=[Person, {"type": "number"}]
    )

    instance = validator([{"firstName": "winner", "lastName": "Dinosaur"}, "fried"])
    with pytest.raises(ValidationError):
        instance.validate()

    instance = validator([{"firstName": "winner", "lastName": "Dinosaur"}, 12324])
    instance.validate()


def test_validate_arrays_nested():

    validator = ArrayWrapper.create(
        "test", item_constraint={"type": "array", "items": {"type": "integer"}}
    )

    instance = validator([[1, 2, 4, 5], [1, 2, 4]])
    instance.validate()

    instance = validator([[1, 2, "h", 5], [1, 2, 4]])
    with pytest.raises(ValidationError):
        instance.validate()

    instance = validator([[1, 2, "h", 5], [1, 2, "4"]])
    with pytest.raises(ValidationError):
        instance.validate()


def test_validate_arrays_length():
    validator = ArrayWrapper.create("test", minItems=1, maxItems=3)

    instance = validator(range(1))
    instance.validate()

    instance = validator(range(2))
    instance.validate()

    instance = validator(range(3))
    instance.validate()

    instance = validator(range(4))
    with pytest.raises(ValidationError):
        instance.validate()

    instance = validator([])
    with pytest.raises(ValidationError):
        instance.validate()


def test_validate_arrays_uniqueness():
    validator = ArrayWrapper.create("test", uniqueItems=True)

    instance = validator([])
    instance.validate()

    instance = validator([1, 2, 3, 4])
    instance.validate()

    instance = validator([1, 2, 2, 4])
    with pytest.raises(ValidationError):
        instance.validate()
