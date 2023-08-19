import copy
import json
import pprint

import jsonschema

import python_jsonschema_objects as pjs

pp = pprint.PrettyPrinter(indent=2)

lpid_class_schema = {
    "$id": "https://example.com/schema-repository/lpid",
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "title": "Logical Process ID",
    "properties": {"lpid_str": {"type": "string"}},
    "required": ["lpid_str"],
    "additionalProperties": True,
}


class A(object):
    a_str = None

    def __init__(self, a_str):
        self.a_str = a_str


def test_regression_185_deepcopy():
    # Class building and instantiation work great and round-trip.
    lpid_class_builder = pjs.ObjectBuilder(lpid_class_schema)
    LPID = lpid_class_builder.classes.LogicalProcessId
    lpid = LPID(lpid_str="foobaz")
    instance = json.loads(lpid.serialize())
    jsonschema.validate(lpid_class_schema, instance)

    # Deep-copying seems to work with instances of normal popos.
    a = A(a_str="barqux")
    assert a
    a_2 = copy.deepcopy(a)
    assert a_2

    # But deep-copying with objects of generated classes doesn't terminate.
    lpid_2 = copy.deepcopy(lpid)
    assert repr(lpid_2) == repr(lpid)
