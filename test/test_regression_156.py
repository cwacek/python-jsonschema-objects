import pytest  # noqa
import python_jsonschema_objects as pjo


def test_regression_156(markdown_examples):
    builder = pjo.ObjectBuilder(
        markdown_examples["MultipleObjects"], resolved=markdown_examples
    )
    classes = builder.build_classes(named_only=True)

    er = classes.ErrorResponse(message="Danger!", status=99)
    vgr = classes.VersionGetResponse(local=False, version="1.2.3")

    # round-trip serialize-deserialize into named classes
    classes.ErrorResponse.from_json(er.serialize())
    classes.VersionGetResponse.from_json(vgr.serialize())

    # round-trip serialize-deserialize into class defined with `oneOf`
    classes.Multipleobjects.from_json(er.serialize())
    classes.Multipleobjects.from_json(vgr.serialize())
