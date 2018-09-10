import python_jsonschema_objects as pjs
import python_jsonschema_objects.wrapper_types


def test_limited_validation(mocker):
    schema = {
        "title": "Example Schema",
        "type": "object",
        "properties": {
            "a": {"type": "array", "items": {"type": "string"}, "default": []}
        },
    }

    ob = pjs.ObjectBuilder(schema)
    ns1 = ob.build_classes()
    validator = ns1.ExampleSchema.a.info["validator"]([])
    validate_items = mocker.patch.object(
        validator, "validate_items", side_effect=validator.validate_items
    )
    validate = mocker.patch.object(
        validator, "validate", side_effect=validator.validate
    )
    mocker.patch.dict(
        ns1.ExampleSchema.a.info,
        {"validator": mocker.MagicMock(return_value=validator)},
    )

    foo = ns1.ExampleSchema()
    # We expect validation to be called on creation
    assert validate_items.call_count == 1

    # We expect manipulation to not revalidate immediately without strict
    foo.a.append("foo")
    foo.a.append("bar")
    assert validate_items.call_count == 1

    # We expect accessing data elements to cause a revalidate, but only the first time
    print(foo.a[0])
    assert validate_items.call_count == 2

    print(foo.a)
    assert foo.a == ["foo", "bar"]
    assert validate_items.call_count == 2


def test_strict_validation(mocker):
    """ Validate that when specified as strict, validation still occurs on every change"""
    schema = {
        "title": "Example Schema",
        "type": "object",
        "properties": {
            "a": {"type": "array", "items": {"type": "string"}, "default": []}
        },
    }

    ob = pjs.ObjectBuilder(schema)
    ns1 = ob.build_classes(strict=True)
    validator = ns1.ExampleSchema.a.info["validator"]([])
    validate_items = mocker.patch.object(
        validator, "validate_items", side_effect=validator.validate_items
    )
    validate = mocker.patch.object(
        validator, "validate", side_effect=validator.validate
    )
    mocker.patch.dict(
        ns1.ExampleSchema.a.info,
        {"validator": mocker.MagicMock(return_value=validator)},
    )

    foo = ns1.ExampleSchema()
    # We expect validation to be called on creation
    assert validate_items.call_count == 1

    # We expect manipulation to revalidate immediately with strict
    foo.a.append("foo")
    foo.a.append("bar")
    assert validate_items.call_count == 3

    # We expect accessing data elements to not revalidate because strict would have revalidated on load
    print(foo.a[0])
    print(foo.a)
    assert foo.a == ["foo", "bar"]
