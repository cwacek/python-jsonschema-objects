import python_jsonschema_objects as pjs
import requests

import pytest

"""
This test is expected to fail because the any_of flag is not set.
"""


def test_297_expect_fail_without_anyof_flag():
    schema = requests.get("https://adaptivecards.io/schemas/adaptive-card.json").json()
    builder = pjs.ObjectBuilder(schema)
    with pytest.raises(NotImplementedError):
        builder.build_classes()


"""
This test is expected to pass because the any_of flag is set.
"""


def test_should_work_with_anyof_flag_set():
    schema = requests.get("https://adaptivecards.io/schemas/adaptive-card.json").json()
    builder = pjs.ObjectBuilder(schema)
    ns = builder.build_classes(any_of="use-first")
