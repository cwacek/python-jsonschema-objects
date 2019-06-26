import python_jsonschema_objects as pjs


def test_nested_arrays_work_fine():
    schema = {
        "title": "Example Schema",
        "type": "object",
        "properties": {
            "a": {"type": "array", "items": {"type": "string"}, "default": []}
        },
    }

    ns1 = pjs.ObjectBuilder(schema).build_classes()

    foo = ns1.ExampleSchema()
    foo.a.append("foo")
    print(foo.for_json())

    assert foo.a == ["foo"]

    bar = ns1.ExampleSchema()
    bar.a.append("bar")
    print(bar.for_json())

    assert bar.a == ["bar"]
