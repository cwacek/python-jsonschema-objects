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

    mockAW = mocker.patch.object(
        python_jsonschema_objects.wrapper_types, 'ArrayWrapper', 
        wraps=python_jsonschema_objects.wrapper_types.ArrayWrapper
        )

    ob = pjs.ObjectBuilder(schema)
    ns1 = ob.build_classes()
    import pdb; pdb.set_trace()

    foo = ns1.ExampleSchema()
    foo.a.append('foo')
    print(foo.for_json())
