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
                                "pattern": r"^(?:(?:\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.){3}(?:\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])$",  # noqa: E501
                            },
                            {
                                "type": "string",
                                "pattern": r"^((([0-9A-Fa-f]{1,4}:){1,6}:)|(([0-9A-Fa-f]{1,4}:){7}))([0-9A-Fa-f]{1,4})$",  # noqa: E501
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
