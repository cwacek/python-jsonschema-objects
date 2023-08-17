import pytest
import python_jsonschema_objects as pjo


def test_114():
    schema = {
        "title": "Example",
        "type": "object",
        "properties": {
            "test_regression_114_anon_array": {
                "type": "array",
                "items": [
                    {
                        "oneOf": [
                            {
                                "type": "string",
                                "pattern": "^(?:(?:\\d|[1-9]\\d|1\\d\\d|2[0-4]\\d|25[0-5])\\.){3}(?:\\d|[1-9]\\d|1\\d\\d|2[0-4]\\d|25[0-5])$",
                            },
                            {
                                "type": "string",
                                "pattern": "^((([0-9A-Fa-f]{1,4}:){1,6}:)|(([0-9A-Fa-f]{1,4}:){7}))([0-9A-Fa-f]{1,4})$",
                            },
                        ]
                    }
                ],
            }
        },
    }

    builder = pjo.ObjectBuilder(schema)
    test = builder.build_classes()
    assert test
