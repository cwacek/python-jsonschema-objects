import pytest

import json
import pkg_resources
import os
import python_jsonschema_objects as pjs
import python_jsonschema_objects.markdown_support


@pytest.fixture
def markdown_examples():
    md = pkg_resources.resource_filename(
        "python_jsonschema_objects.examples", "README.md"
    )
    examples = python_jsonschema_objects.markdown_support.extract_code_blocks(md)
    examples = {json.loads(v)["title"]: json.loads(v) for v in examples["schema"]}
    return examples


@pytest.fixture(autouse=True)
def inject_examples(doctest_namespace, markdown_examples):
    doctest_namespace["examples"] = markdown_examples


@pytest.fixture
def Person(markdown_examples):
    builder = pjs.ObjectBuilder(
        markdown_examples["Example Schema"], resolved=markdown_examples
    )
    assert builder
    return builder.classes["ExampleSchema"]
