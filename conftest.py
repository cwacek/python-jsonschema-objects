import importlib.resources
import json

import pkg_resources
import pytest

import python_jsonschema_objects as pjs


@pytest.fixture
def markdown_examples():
    # FIXME: Remove md_old and examples_old after checking the new way against them.
    md_old = pkg_resources.resource_filename(
        "python_jsonschema_objects.examples", "README.md"
    )
    examples_old = pjs.markdown_support.extract_code_blocks(md_old)

    with importlib.resources.path(
        "python_jsonschema_objects.examples", "README.md"
    ) as md:
        examples = pjs.markdown_support.extract_code_blocks(md)

    assert examples == examples_old

    return {json.loads(v)["title"]: json.loads(v) for v in examples["schema"]}


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
