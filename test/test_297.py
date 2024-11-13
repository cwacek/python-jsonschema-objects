import json
import os.path

import python_jsonschema_objects as pjs

import pytest


@pytest.fixture()
def adaptive_card_schema(request) -> dict:
    with open(
        os.path.join(os.path.dirname(request.path), "resources", "adaptive-card.json")
    ) as f:
        return json.load(f)


"""
This test is expected to fail because the any_of flag is not set.
"""


def test_297_expect_fail_without_anyof_flag(adaptive_card_schema):
    builder = pjs.ObjectBuilder(adaptive_card_schema)
    with pytest.raises(NotImplementedError):
        builder.build_classes()


@pytest.mark.xfail(
    reason="Microsoft apparently doesn't care about valid schemas: https://github.com/microsoft/AdaptiveCards/discussions/8943"
)
def test_should_work_with_anyof_flag_set(adaptive_card_schema):
    builder = pjs.ObjectBuilder(adaptive_card_schema)
    ns = builder.build_classes(any_of="use-first")
