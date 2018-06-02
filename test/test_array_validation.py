# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
import pytest

import python_jsonschema_objects as pjo
import json


@pytest.fixture
def base_schema():
    return {
        "title": "example",
        "type": "object",
        "properties": {
            "input": {"type": "array", "items": {"type": "string"}}
        }
    }


def without_correction(base_schema):
    """ input is a string """
    builder = pjo.ObjectBuilder(base_schema)
    ns = builder.build_classes()

    t = ns.Example(input=["a", "b"])
    assert t.input.data == ["a", "b"]
    t.validate()
    assert t.input.data.data == ["a", "b"]
    t.validate()
    assert t.input.data.data.data == ["a", "b"]


def test_correction(base_schema):
    builder = pjo.ObjectBuilder(base_schema)
    ns = builder.build_classes()

    t = ns.Example(input=["a", "b"])
    assert t.input.data == ["a", "b"]
    t.validate()
    assert t.input.data == ["a", "b"]
    t.validate()
    assert t.input.data == ["a", "b"]

if __name__ == '__main__':
    #without_correction(base_schema())
    test_correction(base_schema())
