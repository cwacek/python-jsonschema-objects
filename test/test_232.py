import json

import python_jsonschema_objects as pjo


def test_default_objects():
    schema = {
        "title": "Example",
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "default": "https://example.com/your-username/my-project",
            },
            "type": {"type": "string", "default": "git"},
        },
    }

    ob = pjo.ObjectBuilder(schema)
    ns1 = ob.build_classes()
    ex = ns1.Example()
    assert ex.url == "https://example.com/your-username/my-project"
    assert ex.type == "git"

    data = {"url": "https://example.com/your-username/my-project2", "type": "hg"}
    ex2 = ns1.Example.from_json(json.dumps(data))
    assert ex2.url == "https://example.com/your-username/my-project2"
    assert ex2.type == "hg"
