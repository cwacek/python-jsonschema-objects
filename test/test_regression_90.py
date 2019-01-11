import python_jsonschema_objects as pjs


def test_null_type():

    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Example1",
        "type": "object",
        "properties": {"foo": {"type": "null"}},
        "required": ["foo"],
    }

    ns1 = pjs.ObjectBuilder(schema).build_classes(strict=True)
    ns1.Example1(foo=None)


def test_null_type_one_of():

    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Example1",
        "type": "object",
        "properties": {"foo": {"oneOf": [{"type": "string"}, {"type": "null"}]}},
        "required": ["foo"],
    }

    ns1 = pjs.ObjectBuilder(schema).build_classes(strict=True)
    ns1.Example1(foo="bar")
    ns1.Example1(foo=None)
