import pytest

import python_jsonschema_objects as pjs


def test_multiple_objects_are_defined(markdown_examples):
    builder = pjs.ObjectBuilder(
        markdown_examples["MultipleObjects"], resolved=markdown_examples
    )

    assert builder
    classes = builder.build_classes()
    assert "ErrorResponse" in classes
    assert "VersionGetResponse" in classes
    print(dir(classes))
