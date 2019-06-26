import pytest  # noqa
from jsonschema import RefResolver, Draft3Validator
from jsonschema._utils import load_schema, URIDict
import python_jsonschema_objects as pjo


def test_non_default_resolver_validator(markdown_examples):
    ms = URIDict()
    draft3 = load_schema("draft3")
    draft4 = load_schema("draft4")
    ms[draft3["id"]] = draft3
    ms[draft4["id"]] = draft4
    resolver_with_store = RefResolver(draft3["id"], draft3, ms)

    # 'Other' schema should be valid with draft3
    builder = pjo.ObjectBuilder(
        markdown_examples["Other"],
        resolver=resolver_with_store,
        validatorClass=Draft3Validator,
        resolved=markdown_examples,
    )
    klasses = builder.build_classes()
    a = klasses.Other(MyAddress="where I live")
    assert a.MyAddress == "where I live"
