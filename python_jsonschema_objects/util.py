import copy
import json


class ArrayValidator(object):

    def __init__(self, ary):
        self.data = ary

    def validate(self):
        import classbuilder
        import validators
        if not isinstance(self.__itemtype__, (tuple, list)):
            self.__itemtype__ = [
                self.__itemtype__ for x in xrange(len(self.data))]

        if len(self.__itemtype__) > len(self.data):
          raise validators.ValidationError(
              "Array does not have sufficient elements to validate against {0}"
              .format(self.__itemtype__))

        for i, elem in enumerate(self.data):
            try:
              typ = self.__itemtype__[i]
            except IndexError:
              pass  # It's actually permissible to run over a tuple constraint.

            if isinstance(typ, dict):
                for param, paramval in typ.iteritems():
                    validator = getattr(validators, param, None)
                    if validator is not None:
                        if param == 'minimum':
                            validator(paramval, elem,
                                      info.get('exclusiveMinimum',
                                               False))
                        elif param == 'maximum':
                            validator(paramval, elem,
                                      info.get('exclusiveMaximum',
                                               False))
                        else:
                            validator(paramval, elem)

            elif issubclass(typ, classbuilder.ProtocolBase):
                val = typ(**elem)
                val.validate()
            elif issubclass(typ, ArrayValidator):
                val = typ(elem)
                val.validate()

    @staticmethod
    def create(name, item_constraint=None, addl_constraints={}):
        """ Create an array validator based on the passed in constraints.

        If item_constraint is a tuple, it is assumed that tuple validation
        is being performed. If it is a class or dictionary, list validation
        will be performed. Classes are assumed to be subclasses of ProtocolBase,
        while dictionaries are expected to be basic types ('string', 'number', ...).

        addl_constraints is expected to be key-value pairs of any of the other
        constraints permitted by JSON Schema v4.
        """
        import classbuilder
        props = {}

        if item_constraint is not None:
          if isinstance(item_constraint, (tuple, list)):
              for i, elem in enumerate(item_constraint):
                  isdict = isinstance(elem, (dict,))
                  isklass = isinstance(elem, type) and issubclass(elem, classbuilder.ProtocolBase)
                  if not any([isdict, isklass]):
                      raise TypeError("Item constraint (position {0}) was not a schema".format(i))
          else:
              isdict = isinstance(item_constraint, (dict,))
              isklass = isinstance(item_constraint, type) and issubclass(item_constraint, classbuilder.ProtocolBase)
              if not any([isdict, isklass]):
                  raise TypeError("Item constraint was not a schema")

              if isdict and item_constraint['type'] == 'array':
                  import pdb; pdb.set_trace()
                  item_constraint = ArrayValidator.create(name + "#sub",
                      item_constraint=item_constraint['items'],
                      addl_constraints=item_constraint)


        props['__itemtype__'] = item_constraint

        props.update(addl_constraints)

        validator = type(name, (ArrayValidator,), props)

        return validator


class ProtocolJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        import classbuilder
        if isinstance(obj, classbuilder.ProtocolBase):
            props = {}
            for raw, trans in obj.__prop_names__.iteritems():
                props[raw] = getattr(obj, trans)
                if props[raw] is None:
                    del props[raw]
            return props
        else:
            return json.JSONEncoder.default(self, obj)


def propmerge(into, data_from):
    """ Merge JSON schema requirements into a dictionary """
    newprops = copy.deepcopy(into)

    for prop, propval in data_from.iteritems():
        if prop not in newprops:
            newprops[prop] = propval
            continue

        new_sp = newprops[prop]
        for subprop, spval in propval.iteritems():
            if subprop not in new_sp:
                new_sp[subprop] = spval

            elif subprop == 'enum':
                new_sp[subprop] = set(spval) & set(new_sp[subprop])

            elif subprop == 'type':
                if spval != new_sp[subprop]:
                    raise TypeError("Type cannot conflict in allOf'")

            elif subprop in ('minLength', 'minimum'):
                new_sp[subprop] = (new_sp[subprop] if
                                   new_sp[subprop] > spval else spval)
            elif subprop in ('maxLength', 'maximum'):
                new_sp[subprop] = (new_sp[subprop] if
                                   new_sp[subprop] < spval else spval)
            elif subprop == 'multipleOf':
                if new_sp[subprop] % spval == 0:
                    new_sp[subprop] = spval
                else:
                    raise AttributeError(
                        "Cannot set conflicting multipleOf values")
            else:
                new_sp[subprop] = spval

        newprops[prop] = new_sp

    return newprops


def resolve_ref_uri(base, ref):
    if ref[0] == '#':
    # Local ref
        uri = base
        if len(uri) > 0 and uri[-1] == '#':
            uri += ref[1:]
        else:
            uri += ref

    else:
        uri = ref

    return uri
"""namespace module"""

__all__ = ("Namespace", "as_namespace")

from collections import Mapping, Sequence


class _Dummy:
    pass
CLASS_ATTRS = dir(_Dummy)
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

    #------------------------
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

    #------------------------
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
