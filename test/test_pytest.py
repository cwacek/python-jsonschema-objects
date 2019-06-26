import pytest

import json
import six
import jsonschema
import python_jsonschema_objects as pjs

import logging

logging.basicConfig(level=logging.DEBUG)


def test_schema_validation():
    """ Test that the ObjectBuilder validates the schema itself.
    """
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "$id": "test",
        "type": "object",
        "properties": {
            "name": "string",
            "email": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
        },
        "required": ["email"],
    }
    with pytest.raises(jsonschema.ValidationError):
        pjs.ObjectBuilder(schema)


def test_regression_9():
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "$id": "test",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
        },
        "required": ["email"],
    }
    builder = pjs.ObjectBuilder(schema)
    builder.build_classes()


def test_build_classes_is_idempotent():
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "title": "test",
        "type": "object",
        "properties": {
            "name": {"$ref": "#/definitions/foo"},
            "email": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
        },
        "required": ["email"],
        "definitions": {
            "reffed": {"type": "string"},
            "foo": {"type": "array", "items": {"$ref": "#/definitions/reffed"}},
        },
    }
    builder = pjs.ObjectBuilder(schema)
    x = builder.build_classes()
    builder.build_classes()


def test_underscore_properties():
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "title": "AggregateQuery",
        "type": "object",
        "properties": {"group": {"type": "object", "properties": {}}},
    }

    builder = pjs.ObjectBuilder(schema)
    ns = builder.build_classes()
    my_obj_type = ns.Aggregatequery
    request_object = my_obj_type(
        group={
            "_id": {"foo_id": "$foo_id", "foo_type": "$foo_type"},
            "foo": {"$sum": 1},
        }
    )

    assert request_object.group._id == {"foo_id": "$foo_id", "foo_type": "$foo_type"}


def test_array_regressions():
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "$id": "test",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email_aliases": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/foo"},
                },
            },
        },
        "definitions": {"foo": {"type": "string"}},
    }
    builder = pjs.ObjectBuilder(schema)

    ns = builder.build_classes()

    x = ns.Test.from_json(
        """{"email_aliases": {
            "Freddie": ["james", "bond"]
            }}"""
    )
    x.validate()

    y = ns.Test(email_aliases={"Freddie": ["james", "bond"]})
    y.validate()


def test_arrays_can_have_reffed_items_of_mixed_type():
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "$id": "test",
        "type": "object",
        "properties": {
            "list": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {"$ref": "#/definitions/foo"},
                        {
                            "type": "object",
                            "properties": {"bar": {"type": "string"}},
                            "required": ["bar"],
                        },
                    ]
                },
            }
        },
        "definitions": {"foo": {"type": "string"}},
    }
    builder = pjs.ObjectBuilder(schema)
    ns = builder.build_classes()

    ns.Test(list=["foo", "bar"])
    ns.Test(list=[{"bar": "nice"}, "bar"])
    with pytest.raises(pjs.ValidationError):
        ns.Test(list=[100])


def test_regression_39():
    builder = pjs.ObjectBuilder("test/thing-two.json")
    ns = builder.build_classes()

    for thing in ("BarMessage", "BarGroup", "Bar", "Header"):
        assert thing in ns

    x = ns.BarMessage(
        id="message_id", title="my bar group", bars=[{"name": "Freddies Half Shell"}]
    )

    x.validate()

    # Now an invalid one
    with pytest.raises(pjs.ValidationError):
        ns.BarMessage(
            id="message_id",
            title="my bar group",
            bars=[{"Address": "I should have a name"}],
        )


def test_loads_markdown_schema_extraction(markdown_examples):
    assert "Other" in markdown_examples


def test_object_builder_loads_memory_references(markdown_examples):
    builder = pjs.ObjectBuilder(markdown_examples["Other"], resolved=markdown_examples)
    assert builder

    with pytest.raises(pjs.ValidationError):
        builder.validate({"MyAddress": 1234})

    builder.validate({"MyAddress": "1234"})


def test_object_builder_reads_all_definitions(markdown_examples):
    for nm, ex in six.iteritems(markdown_examples):
        builder = pjs.ObjectBuilder(ex, resolved=markdown_examples)
        assert builder


@pytest.fixture
def oneOf(markdown_examples):
    builder = pjs.ObjectBuilder(markdown_examples["OneOf"], resolved=markdown_examples)
    return builder.classes["Oneof"]


@pytest.mark.parametrize(
    "json_object", ['{"MyData": "an address"}', '{"MyData": "1234"}']
)
def test_oneOf_validates_against_any_valid(oneOf, json_object):

    oneOf.from_json(json_object)


def test_oneOf_fails_against_non_matching(oneOf):
    with pytest.raises(pjs.ValidationError):
        oneOf.from_json('{"MyData": 1234.234}')


@pytest.fixture
def oneOfBare(markdown_examples):
    builder = pjs.ObjectBuilder(
        markdown_examples["OneOfBare"], resolved=markdown_examples
    )
    return builder.classes["Oneofbare"]


@pytest.mark.parametrize(
    "json_object",
    ['{"MyAddress": "an address"}', '{"firstName": "John", "lastName": "Winnebago"}'],
)
def test_oneOfBare_validates_against_any_valid(oneOfBare, json_object):

    oneOfBare.from_json(json_object)


def test_oneOfBare_fails_against_non_matching(oneOfBare):
    with pytest.raises(pjs.ValidationError):
        oneOfBare.from_json('{"MyData": 1234.234}')


@pytest.fixture
def Other(markdown_examples):
    builder = pjs.ObjectBuilder(markdown_examples["Other"], resolved=markdown_examples)
    assert builder
    return builder.classes["Other"]


def test_additional_props_allowed_by_default(Person):
    person = Person()
    person.randomAttribute = 4
    assert int(person.randomAttribute) == 4


def test_additional_props_permitted_explicitly(markdown_examples):
    builder = pjs.ObjectBuilder(
        markdown_examples["AddlPropsAllowed"], resolved=markdown_examples
    )
    assert builder

    test = builder.classes["Addlpropsallowed"]()
    test.randomAttribute = 40
    assert int(test.randomAttribute) == 40


def test_still_raises_when_accessing_undefined_attrs(Person):

    person = Person()
    person.firstName = "James"

    # If the attribute doesn't exist, we expect an AttributeError
    with pytest.raises(AttributeError):
        print(person.randomFoo)

    # If the attribute is literal-esq, isn't set but isn't required, accessing it should be fine
    assert person.gender == None

    # If the attribute is an object, isn't set, but isn't required accessing it should throw an exception
    with pytest.raises(AttributeError) as e:
        print(person.address.street)
        assert "'NoneType' object has no attribute 'street'" in e


def test_permits_deletion_of_additional_properties(Person):
    person = Person()
    person.randomthing = 44
    assert int(person.randomthing) == 44

    del person["randomthing"]

    with pytest.raises(AttributeError):
        assert person.randomthing is None


def test_additional_props_disallowed_explicitly(Other):

    other = Other()
    with pytest.raises(pjs.ValidationError):
        other.randomAttribute = 4


def test_objects_can_be_empty(Person):
    assert Person()


def test_object_equality_should_compare_data(Person):
    person = Person(firstName="john")
    person2 = Person(firstName="john")

    assert person == person2

    person2.lastName = "Wayne"
    assert person != person2


def test_object_allows_attributes_in_oncstructor(Person):
    person = Person(firstName="James", lastName="Bond", age=35)

    assert person
    assert str(person.firstName) == "James"
    assert str(person.lastName) == "Bond"
    assert int(person.age) == 35


def test_object_validates_on_json_decode(Person):
    with pytest.raises(pjs.ValidationError):
        Person.from_json('{"firstName": "James"}')


def test_object_validates_enumerations(Person):
    person = Person()

    with pytest.raises(pjs.ValidationError):
        person.gender = "robot"

    person.gender = "male"
    person.gender = "female"


def test_validation_of_mixed_type_enums(Person):
    person = Person()

    person.deceased = "yes"
    person.deceased = "no"
    person.deceased = 1

    with pytest.raises(pjs.ValidationError):
        person.deceased = "robot"

    with pytest.raises(pjs.ValidationError):
        person.deceased = 2

    with pytest.raises(pjs.ValidationError):
        person.deceased = 2.3


def test_objects_allow_non_required_attrs_to_be_missing(Person):
    person = Person(firstName="James", lastName="Bond")

    assert person
    assert str(person.firstName) == "James"
    assert str(person.lastName) == "Bond"


def test_objects_require_required_attrs_on_validate(Person):
    person = Person(firstName="James")

    assert person

    with pytest.raises(pjs.ValidationError):
        person.validate()


@pytest.fixture(scope="function")
def person_object(Person):
    return Person(firstName="James")


def test_attribute_access_via_dict(person_object):
    name = person_object["firstName"]
    assert str(name) == "James"


def test_attribute_set_via_dict(person_object):
    person_object["firstName"] = "John"

    name = person_object["firstName"]
    assert str(name) == "John"


def test_numeric_attribute_validation(Person):
    with pytest.raises(pjs.ValidationError):
        Person(firstName="James", lastName="Bond", age=-10)

    p = Person(firstName="James", lastName="Bond")
    with pytest.raises(pjs.ValidationError):
        p.age = -1


def test_objects_validate_prior_to_serializing(Person):
    p = Person(firstName="James", lastName="Bond")

    p._properties["age"] = -1

    with pytest.raises(pjs.ValidationError):
        p.serialize()


def test_serializing_removes_null_objects(Person):
    person = Person(firstName="James", lastName="Bond")

    json_str = person.serialize()
    assert "age" not in json.loads(json_str)


def test_lists_get_serialized_correctly(Person):
    person = Person(firstName="James", lastName="Bond", dogs=["Lassie", "Bobo"])

    json_str = person.serialize()
    assert json.loads(json_str) == {
        "firstName": "James",
        "lastName": "Bond",
        "dogs": ["Lassie", "Bobo"],
    }


@pytest.mark.parametrize(
    "pdict",
    [
        dict(firstName="James", lastName="Bond", dogs=["Lassie", "Bobo"]),
        dict(
            firstName="James",
            lastName="Bond",
            address={
                "street": "10 Example Street",
                "city": "Springfield",
                "state": "USA",
            },
            dogs=["Lassie", "Bobo"],
        ),
    ],
)
def test_dictionary_transformation(Person, pdict):

    person = Person(**pdict)

    assert person.as_dict() == pdict


def test_strict_mode():
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {"firstName": {"type": "string"}, "lastName": {"type": "string"}},
        "$id": "test",
        "title": "Name Data",
        "required": ["firstName"],
    }
    builder = pjs.ObjectBuilder(schema)
    ns = builder.build_classes()  # by defualt strict = False
    NameData = ns.NameData
    # no strict flag - so should pass even no firstName
    NameData(lastName="hello")
    with pytest.raises(pjs.ValidationError):
        ns = builder.build_classes(strict=True)
        NameData = ns.NameData
        NameData(lastName="hello")


def test_boolean_in_child_object():
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "$id": "test",
        "type": "object",
        "properties": {"data": {"type": "object", "additionalProperties": True}},
    }
    builder = pjs.ObjectBuilder(schema)
    ns = builder.build_classes()

    ns.Test(data={"my_bool": True})


@pytest.mark.parametrize(
    "default",
    [
        '{"type": "boolean", "default": false}',
        '{"type": "string", "default": "Hello"}',
        '{"type": "integer", "default": 500}',
    ],
)
def test_default_values(default):
    default = json.loads(default)
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "$id": "test",
        "type": "object",
        "properties": {"sample": default},
    }

    builder = pjs.ObjectBuilder(schema)
    ns = builder.build_classes()

    x = ns.Test()
    assert x.sample == default["default"]
