import pytest  # noqa
import python_jsonschema_objects as pjo


def test_circular_references(markdown_examples):

    builder = pjo.ObjectBuilder(markdown_examples["Circular References"])
    klasses = builder.build_classes()
    a = klasses.A()
    b = klasses.B()
    a.message = "foo"
    b.author = "James Dean"
    a.reference = b
    a.reference = b

    assert a.reference == b
    assert b.oreference == None  # noqa
    assert a.message == "foo"

    serialized = a.serialize(sort_keys=True)
    assert (
        serialized == '{"message": "foo", "reference": {"author": "James Dean"}}'
    )  # noqa
