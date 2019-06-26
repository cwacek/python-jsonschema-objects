import six
import copy
import json


class lazy_format(object):
    __slots__ = ("fmt", "args", "kwargs")

    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.fmt.format(*self.args, **self.kwargs)


def safe_issubclass(x, y):
    """Safe version of issubclass() that will not throw TypeErrors.

    Invoking issubclass('object', some-abc.meta instances) will result
    in the underlying implementation throwing TypeError's from trying to
    memoize the result- 'object' isn't a usable weakref target at that level.
    Unfortunately this gets exposed all the way up to our code; thus a
    'safe' version of the function."""
    try:
        return issubclass(x, y)
    except TypeError:
        return False


def coerce_for_expansion(mapping):
    """Given a value, make sure it is usable for f(**val) expansion.

    In py2.7, the value must be a dictionary- thus a as_dict() method
    will be invoked if available.  In py3k, the raw mapping is returned
    unmodified."""
    if six.PY2 and hasattr(mapping, "as_dict"):
        return mapping.as_dict()
    return mapping


class ProtocolJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        from python_jsonschema_objects import classbuilder
        from python_jsonschema_objects import wrapper_types

        if isinstance(obj, classbuilder.LiteralValue):
            return obj._value
        if isinstance(obj, wrapper_types.ArrayWrapper):
            return obj.for_json()
        if isinstance(obj, classbuilder.ProtocolBase):
            props = {}
            for raw, trans in six.iteritems(obj.__prop_names__):
                props[raw] = getattr(obj, trans)
                if props[raw] is None:
                    del props[raw]
            for raw, data in six.iteritems(obj._extended_properties):
                props[raw] = data
                if props[raw] is None:
                    del props[raw]
            return props
        else:
            return json.JSONEncoder.default(self, obj)


def propmerge(into, data_from):
    """ Merge JSON schema requirements into a dictionary """
    newprops = copy.deepcopy(into)

    for prop, propval in six.iteritems(data_from):
        if prop not in newprops:
            newprops[prop] = propval
            continue

        new_sp = newprops[prop]
        for subprop, spval in six.iteritems(propval):
            if subprop not in new_sp:
                new_sp[subprop] = spval

            elif subprop == "enum":
                new_sp[subprop] = set(spval) & set(new_sp[subprop])

            elif subprop == "type":
                if spval != new_sp[subprop]:
                    raise TypeError("Type cannot conflict in allOf'")

            elif subprop in ("minLength", "minimum"):
                new_sp[subprop] = new_sp[subprop] if new_sp[subprop] > spval else spval
            elif subprop in ("maxLength", "maximum"):
                new_sp[subprop] = new_sp[subprop] if new_sp[subprop] < spval else spval
            elif subprop == "multipleOf":
                if new_sp[subprop] % spval == 0:
                    new_sp[subprop] = spval
                else:
                    raise AttributeError("Cannot set conflicting multipleOf values")
            else:
                new_sp[subprop] = spval

        newprops[prop] = new_sp

    return newprops


def resolve_ref_uri(base, ref):
    if ref[0] == "#":
        # Local ref
        uri = base.rsplit("#", 1)[0] + ref
    else:
        uri = ref

    return uri


"""namespace module"""

__all__ = ("Namespace", "as_namespace")

from collections import Mapping, Sequence


class _Dummy:
    pass


CLASS_ATTRS = dir(_Dummy)
NEWCLASS_ATTRS = dir(object)
del _Dummy


class Namespace(dict):

    """A dict subclass that exposes its items as attributes.

    Warning: Namespace instances do not have direct access to the
    dict methods.

    """

    def __init__(self, obj={}):
        dict.__init__(self, obj)

    def __dir__(self):
        return list(self)

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, super(dict, self).__repr__())

    def __getattribute__(self, name):
        try:
            return self[name]
        except KeyError:
            msg = "'%s' object has no attribute '%s'"
            raise AttributeError(msg % (type(self).__name__, name))

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]

    # ------------------------
    # "copy constructors"

    @classmethod
    def from_object(cls, obj, names=None):
        if names is None:
            names = dir(obj)
        ns = {name: getattr(obj, name) for name in names}
        return cls(ns)

    @classmethod
    def from_mapping(cls, ns, names=None):
        if names:
            ns = {name: ns[name] for name in names}
        return cls(ns)

    @classmethod
    def from_sequence(cls, seq, names=None):
        if names:
            seq = {name: val for name, val in seq if name in names}
        return cls(seq)

    # ------------------------
    # static methods

    @staticmethod
    def hasattr(ns, name):
        try:
            object.__getattribute__(ns, name)
        except AttributeError:
            return False
        return True

    @staticmethod
    def getattr(ns, name):
        return object.__getattribute__(ns, name)

    @staticmethod
    def setattr(ns, name, value):
        return object.__setattr__(ns, name, value)

    @staticmethod
    def delattr(ns, name):
        return object.__delattr__(ns, name)


def as_namespace(obj, names=None):

    # functions
    if isinstance(obj, type(as_namespace)):
        obj = obj()

    # special cases
    if isinstance(obj, type):
        names = (name for name in dir(obj) if name not in CLASS_ATTRS)
        return Namespace.from_object(obj, names)
    if isinstance(obj, Mapping):
        return Namespace.from_mapping(obj, names)
    if isinstance(obj, Sequence):
        return Namespace.from_sequence(obj, names)

    # default
    return Namespace.from_object(obj, names)
