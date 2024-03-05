import pytest

import python_jsonschema_objects as pjo


def test_const_properties():
    schema = {
        "title": "Example",
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "default": "https://example.com/your-username/my-project",
            },
            "type": {"type": "string", "const": "git"},
        },
    }

    ob = pjo.ObjectBuilder(schema)
    ns1 = ob.build_classes()
    ex = ns1.Example()
    ex.url = "can be anything"

    # we expect the value to be set already for const values
    assert ex.type == "git"
    with pytest.raises(pjo.ValidationError):
        # Trying to set the value to something else should throw validation errors
        ex.type = "mercurial"

    # setting the value to the const value is a no-op, but permitted
    ex.type = "git"


def test_const_bare_type():
    schema = {
        "title": "Example",
        "type": "string",
        "const": "I stand alone",
    }

    ob = pjo.ObjectBuilder(schema)
    ns1 = ob.build_classes()
    ex = ns1.Example("I stand alone")
    # we expect the value to be set already for const values
    assert ex == "I stand alone"
    with pytest.raises(pjo.ValidationError):
        # Trying to set the value to something else should throw validation errors
        ex = ns1.Example("mercurial")

    # setting the value to the const value is a no-op, but permitted
    ex = ns1.Example("I stand alone")
