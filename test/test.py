# coding: spec
# This is a comparison of DSL syntax to what is generated

import nose
import nose.tools

from noseOfYeti.tokeniser.support import noy_sup_setUp
from unittest import TestCase
import nose

import pkg_resources
import python_jsonschema_objects as pjs
import python_jsonschema_objects.markdown_support as markdown_support

describe TestCase, 'it can extract code blocks from metadata':

    before_each:
        md = pkg_resources.resource_filename('python_jsonschema_objects',
                '../README.md')
        self.examples = markdown_support.extract_code_blocks(md)
        import pdb; pdb.set_trace()

    it 'passes':
        pass



"""
import protobuilder
import md_extractor


def test_examples():
    uri = "../../protocol/json/schema.json"
    validator = protobuilder.Validator(uri)

    protocol_examples = md_extractor.extract_examples(
            "../../../README.md")

    for ex in protocol_examples:
        yield assert_json_validates, ex, validator


def assert_json_validates(obj, validator):
    assert validator.validate(obj)
"""
