[![Build Status](https://travis-ci.org/cwacek/python-jsonschema-objects.svg?branch=master)](https://travis-ci.org/cwacek/python-jsonschema-objects)

## What

python-jsonschema-objects provides an *automatic* class-based
binding to JSON schemas for use in python.

For example, given the following schema:

``` schema
{
    "title": "Example Schema",
    "type": "object",
    "properties": {
        "firstName": {
            "type": "string"
        },
        "lastName": {
            "type": "string"
        },
        "age": {
            "description": "Age in years",
            "type": "integer",
            "minimum": 0
        },
        "dogs": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 4
        },
        "address": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"},
                "state": {"type": "string"}
                },
            "required":["street", "city"]
            },
        "gender": {
            "type": "string",
            "enum": ["male", "female"]
        },
        "deceased": {
            "enum": ["yes", "no", 1, 0, "true", "false"]
            }
    },
    "required": ["firstName", "lastName"]
}
```

jsonschema-objects can generate a class based binding. Assume
here that the schema above has been loaded in a variable called
`schema`:

``` python
>>> import python_jsonschema_objects as pjs
>>> builder = pjs.ObjectBuilder(schema)
>>> ns = builder.build_classes()
>>> Person = ns.ExampleSchema
>>> james = Person(firstName="James", lastName="Bond")
>>> james.lastName
u'Bond'
>>> james
<example_schema lastName=Bond age=None firstName=James>
```

Validations will also be applied as the object is manipulated.

``` python
>>> james.age = -2
python_jsonschema_objects.validators.ValidationError: -2 was less
or equal to than 0
```

The object can be serialized out to JSON:

``` python
>>> james.serialize()
'{"lastName": "Bond", "age": null, "firstName": "James"}'
```

## Why

Ever struggled with how to define message formats? Been
frustrated by the difficulty of keeping documentation and message
definition in lockstep? Me too.

There are lots of tools designed to help define JSON object
formats, foremost among them [JSON Schema](http://json-schema.org).
JSON Schema allows you to define JSON object formats, complete
with validations.

However, JSON Schema is language agnostic. It validates encoded
JSON directly - using it still requires an object binding in
whatever language we use. Often writing the binding is just as
tedious as writing the schema itself.

This avoids that problem by auto-generating classes, complete
with validation, directly from an input JSON schema. These
classes can seamlessly encode back and forth to JSON valid
according to the schema.

## Other Features

The ObjectBuilder can be passed a dictionary specifying
'memory' schemas when instantiated. This will allow it to
resolve references where the referenced schemas are retrieved
out of band and provided at instantiation.

For instance:

``` schema
{
    "title": "Address",
    "type": "string"
}
```

``` schema
{
    "title": "AddlPropsAllowed",
    "type": "object",
    "additionalProperties": true
}
```

``` schema
{
    "title": "Other",
    "type": "object",
    "properties": {
        "MyAddress": {"$ref": "memory:Address"}
    },
    "additionalProperties": false
}
```

Generated wrappers can also properly deserialize data
representing 'oneOf' relationships, so long as the candidate
schemas are unique.

``` schema
{
    "title": "Age",
    "type": "integer"
}

```

``` schema
{
    "title": "OneOf",
    "type": "object",
    "properties": {
        "MyData": { "oneOf":[
            {"$ref": "memory:Address"},
            {"$ref": "memory:Age"}
            ]
        }
    },
    "additionalProperties": false
}
```
``` schema
{
    "title": "OneOfBare",
    "type": "object",
    "oneOf":[
            {"$ref": "memory:Other"},
            {"$ref": "memory:Example Schema"}
            ],
    "additionalProperties": false
}
```

## Installation

    pip install python_jsonschema_objects

## Tests

Tests are managed using the excellent Tox. Simply `pip install
tox`, then `tox`.

## Changelog

**0.0.18**

+ Fix assignment to schemas defined using 'oneOf'
+ Add sphinx documentation and support for readthedocs

0.0.16 - Fix behavior of exclusiveMinimum and exclusiveMaximum
validators so that they work properly.

0.0.14 - Roll in a number of fixes from Github contributors,
including fixes for oneOf handling, array validation, and Python
3 support.

0.0.13 - Lazily build object classes. Allows low-overhead use
of jsonschema validators.

0.0.12 - Support "true" as a value for 'additionalProperties'

0.0.11 - Generated wrappers can now properly deserialize data
representing 'oneOf' relationships, so long as the candidate
schemas are unique.

0.0.10 - Fixed incorrect checking of enumerations which
previously enforced that all enumeration values be of the same
type.

0.0.9 - Added support for 'memory:' schema URIs, which can be
used to reference externally resolved schemas.

0.0.8 - Fixed bugs that occurred when the same class was read
from different locations in the schema, and thus had a different
URI

0.0.7 - Required properties containing the '@' symbol no longer
cause `build_classes()` to fail.

0.0.6 - All literals now use a standardized LiteralValue type.
Array validation actually coerces element types. `as_dict` can
translate objects to dictionaries seamlessly.

0.0.5 - Improved validation for additionalItems (and tests to
match). Provided dictionary-syntax access to object properties
and iteration over properties.

0.0.4 - Fixed some bugs that only showed up under specific schema
layouts, including one which forced remote lookups for
schema-local references.

0.0.3b - Fixed ReStructuredText generation

0.0.3 - Added support for other array validations (minItems,
maxItems, uniqueItems).

0.0.2 - Array item type validation now works. Specifying 'items',
will now enforce types, both in the tuple and list syntaxes.

0.0.1 - Class generation works, including 'oneOf' and 'allOf'
relationships. All basic validations work.
