import importlib.resources
import importlib.resources
import json

import pytest

import python_jsonschema_objects as pjs


@pytest.fixture
def markdown_examples():
    if hasattr(importlib.resources, "as_file"):
        filehandle = importlib.resources.as_file(
            importlib.resources.files("python_jsonschema_objects.examples")
            / "README.md"
        )
    else:
        filehandle = importlib.resources.path(
            "python_jsonschema_objects.examples", "README.md"
        )
    with filehandle as md:
        examples = pjs.markdown_support.extract_code_blocks(md)

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
