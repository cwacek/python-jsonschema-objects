import json

import python_jsonschema_objects as pjo


def test_kw_flowthrough():
    with open("resources/lottie.schema.json") as f:
        schema = json.load(f)

    ob = pjo.ObjectBuilder(schema)
    ns1 = ob.build_classes()
    print(ns1.values())
