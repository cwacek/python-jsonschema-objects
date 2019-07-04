import python_jsonschema_objects as pjs
import pytest


@pytest.fixture
def testclass():
    builder = pjs.ObjectBuilder({"title": "Test", "type": "object"})
    ns = builder.build_classes()
    return ns.Test()


def test_extra_properties_can_be_deleted_with_item_syntax(testclass):
    # Deletion before setting should throw attribute errors
    with pytest.raises(AttributeError):
        del testclass["foo"]

    testclass.foo = 42
    assert testclass.foo == 42
    del testclass["foo"]

    # Etestclasstra properties not set should raise AttributeErrors when accessed
    with pytest.raises(AttributeError):
        testclass.foo


def test_extra_properties_can_be_deleted_with_attribute_syntax(testclass):
    # Deletion before setting should throw attribute errors
    with pytest.raises(AttributeError):
        del testclass.foo

    testclass.foo = 42
    assert testclass.foo == 42
    del testclass.foo

    # Extra properties not set should raise AttributeErrors when accessed
    with pytest.raises(AttributeError):
        testclass.foo


def test_extra_properties_can_be_deleted_directly(testclass):
    # Deletion before setting should throw attribute errors
    with pytest.raises(AttributeError):
        delattr(testclass, "foo")

    testclass.foo = 42
    assert testclass.foo == 42
    delattr(testclass, "foo")

    # Extra properties not set should raise AttributeErrors when accessed
    with pytest.raises(AttributeError):
        testclass.foo


def test_unrequired_real_properties_arent_really_deleted(Person):
    p = Person(age=20)

    assert p.age == 20
    del p.age
    assert p.age == None

    p.age = 20
    assert p.age == 20
    delattr(p, "age")
    assert p.age == None

    p.age = 20
    assert p.age == 20
    del p["age"]
    assert p.age == None


def test_required_real_properties_throw_attributeerror_on_delete(Person):
    p = Person(firstName="Fred")

    assert p.firstName == "Fred"
    with pytest.raises(AttributeError):
        del p.firstName

    p.firstName = "Fred"
    assert p.firstName == "Fred"
    with pytest.raises(AttributeError):
        delattr(p, "firstName")

    p.firstName = "Fred"
    assert p.firstName == "Fred"
    with pytest.raises(AttributeError):
        del p["firstName"]
