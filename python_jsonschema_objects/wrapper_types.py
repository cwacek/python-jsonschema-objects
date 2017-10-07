import collections
import logging

import six

from python_jsonschema_objects import util
from python_jsonschema_objects.validators import registry, ValidationError

logger = logging.getLogger(__name__)


class ArrayWrapper(collections.MutableSequence):
    """ A wrapper for array-like structures.

    This implements all of the array like behavior that one would want,
    with a dirty-tracking mechanism to avoid constant validation costs.
    """

    def __len__(self):
        return len(self.data)

    def __delitem__(self, index):
        self.data.remove(index)
        self._dirty = True

    def insert(self, index, value):
        self.data.insert(index, value)
        self._dirty = True

    def __setitem__(self, index, value):
        self.data[index] = value
        self._dirty = True

    def __getitem__(self, idx):
        return self.typed_elems[idx]

    def __eq__(self, other):
        if isinstance(other, ArrayWrapper):
            return self.for_json() == other.for_json()
        else:
            return self.for_json() == other

    def __init__(self, ary):
        if isinstance(ary, (list, tuple, collections.Sequence)):
            self.data = ary
            self._dirty = True
            self._typed = None
        elif isinstance(ary, ArrayWrapper):
            self.data = ary.data
            self._dirty = True
            self._typed = None
        else:
            raise TypeError("Invalid value given to array validator: {0}"
                            .format(ary))

    @property
    def typed_elems(self):
        if self._typed is None or self._dirty is True:
            self._typed = self.validate_items()
            self._dirty = False

        return self._typed

    def __repr__(self):
        return "<%s=%s>" % (
            self.__class__.__name__,
            str(self.data)
        )


    @classmethod
    def from_json(cls, jsonmsg):
        import json
        msg = json.loads(jsonmsg)
        obj = cls(msg)
        obj.validate()
        return obj

    def serialize(self):
        d = self.validate_items()
        enc = util.ProtocolJSONEncoder()
        return enc.encode(d)

    def for_json(self):
        from python_jsonschema_objects import classbuilder

        out = []
        for item in self.typed_elems:
            if isinstance(item, (
                    classbuilder.ProtocolBase,
                    classbuilder.LiteralValue,
                    ArrayWrapper)):
                out.append(item.for_json())
            else:
                out.append(item)

        return out

    def validate(self):
        self.validate_items()
        self.validate_length()
        self.validate_uniqueness()
        return True

    def validate_uniqueness(self):
        from python_jsonschema_objects import classbuilder

        if getattr(self, 'uniqueItems', None) is not None:
            testset = set(self.data)
            if len(testset) != len(self.data):
                raise ValidationError(
                    "{0} has duplicate elements, but uniqueness required"
                    .format(self.data))

    def validate_length(self):
        from python_jsonschema_objects import classbuilder

        if getattr(self, 'minItems', None) is not None:
            if len(self.data) < self.minItems:
                raise ValidationError(
                    "{1} has too few elements. Wanted {0}."
                    .format(self.minItems, self.data))

        if getattr(self, 'maxItems', None) is not None:
            if len(self.data) > self.maxItems:
                raise ValidationError(
                    "{1} has too few elements. Wanted {0}."
                    .format(self.maxItems, self.data))

    def validate_items(self):
        from python_jsonschema_objects import classbuilder

        if self.__itemtype__ is None:
            return

        type_checks = self.__itemtype__
        if not isinstance(type_checks, (tuple, list)):
            # we were given items = {'type': 'blah'} ; thus ensure the type for all data.
            type_checks = [type_checks] * len(self.data)
        elif len(type_checks) > len(self.data):
            raise ValidationError(
                "{1} does not have sufficient elements to validate against {0}"
                .format(self.__itemtype__, self.data))

        typed_elems = []
        for elem, typ in zip(self.data, type_checks):
            if isinstance(typ, dict):
                for param, paramval in six.iteritems(typ):
                    validator = registry(param)
                    if validator is not None:
                        validator(paramval, elem, typ)
                typed_elems.append(elem)

            elif util.safe_issubclass(typ, classbuilder.LiteralValue):
                val = typ(elem)
                val.validate()
                typed_elems.append(val)
            elif util.safe_issubclass(typ, classbuilder.ProtocolBase):
                if not isinstance(elem, typ):
                    try:
                        if isinstance(elem, (six.string_types, six.integer_types, float)):
                            val = typ(elem)
                        else:
                            val = typ(**util.coerce_for_expansion(elem))
                    except TypeError as e:
                        raise ValidationError("'{0}' is not a valid value for '{1}': {2}"
                                              .format(elem, typ, e))
                else:
                    val = elem
                val.validate()
                typed_elems.append(val)

            elif util.safe_issubclass(typ, ArrayWrapper):
                val = typ(elem)
                val.validate()
                typed_elems.append(val)

            elif isinstance(typ, classbuilder.TypeProxy):
                try:
                    if isinstance(elem, (six.string_types, six.integer_types, float)):
                        val = typ(elem)
                    else:
                        val = typ(**util.coerce_for_expansion(elem))
                except TypeError as e:
                    raise ValidationError("'{0}' is not a valid value for '{1}': {2}"
                                          .format(elem, typ, e))
                else:
                    val.validate()
                    typed_elems.append(val)

        return typed_elems

    @staticmethod
    def create(name, item_constraint=None, **addl_constraints):
        """ Create an array validator based on the passed in constraints.

        If item_constraint is a tuple, it is assumed that tuple validation
        is being performed. If it is a class or dictionary, list validation
        will be performed. Classes are assumed to be subclasses of ProtocolBase,
        while dictionaries are expected to be basic types ('string', 'number', ...).

        addl_constraints is expected to be key-value pairs of any of the other
        constraints permitted by JSON Schema v4.
        """
        from python_jsonschema_objects import classbuilder
        klassbuilder = addl_constraints.pop("classbuilder", None)
        props = {}

        if item_constraint is not None:
            if isinstance(item_constraint, (tuple, list)):
                for i, elem in enumerate(item_constraint):
                    isdict = isinstance(elem, (dict,))
                    isklass = isinstance( elem, type) and util.safe_issubclass(
                        elem, (classbuilder.ProtocolBase, classbuilder.LiteralValue))

                    if not any([isdict, isklass]):
                        raise TypeError(
                            "Item constraint (position {0}) is not a schema".format(i))
            elif isinstance(item_constraint, classbuilder.TypeProxy):
                pass
            elif util.safe_issubclass(item_constraint, ArrayWrapper):
                pass
            else:
                isdict = isinstance(item_constraint, (dict,))
                isklass = isinstance( item_constraint, type) and util.safe_issubclass(
                    item_constraint, (classbuilder.ProtocolBase, classbuilder.LiteralValue))

                if not any([isdict, isklass]):
                    raise TypeError("Item constraint is not a schema")

                if isdict and '$ref' in item_constraint:
                    if klassbuilder is None:
                        raise TypeError("Cannot resolve {0} without classbuilder"
                                        .format(item_constraint['$ref']))

                    uri = item_constraint['$ref']
                    if uri in klassbuilder.resolved:
                        logger.debug(util.lazy_format(
                            "Using previously resolved object for {0}", uri))
                    else:
                        logger.debug(util.lazy_format("Resolving object for {0}", uri))

                        with klassbuilder.resolver.resolving(uri) as resolved:
                            # Set incase there is a circular reference in schema definition
                            klassbuilder.resolved[uri] = None
                            klassbuilder.resolved[uri] = klassbuilder.construct(
                                uri,
                                resolved,
                                (classbuilder.ProtocolBase,))

                    item_constraint = klassbuilder.resolved[uri]

                elif isdict and item_constraint.get('type') == 'array':
                    # We need to create a sub-array validator.
                    item_constraint = ArrayWrapper.create(name + "#sub",
                                                          item_constraint=item_constraint[
                                                                'items'],
                                                          addl_constraints=item_constraint)
                elif isdict and 'oneOf' in item_constraint:
                    # We need to create a TypeProxy validator
                    uri = "{0}_{1}".format(name, "<anonymous_list_type>")
                    type_array = []
                    for i, item_detail in enumerate(item_constraint['oneOf']):
                        if '$ref' in item_detail:
                            subtype = klassbuilder.construct(
                                util.resolve_ref_uri(
                                    klassbuilder.resolver.resolution_scope,
                                    item_detail['$ref']),
                                item_detail)
                        else:
                            subtype = klassbuilder.construct(
                                uri + "_%s" % i, item_detail)

                        type_array.append(subtype)

                    item_constraint = classbuilder.TypeProxy(type_array)

                elif isdict and item_constraint.get('type') == 'object':
                    """ We need to create a ProtocolBase object for this anonymous definition"""
                    uri = "{0}_{1}".format(name, "<anonymous_list_type>")
                    item_constraint = klassbuilder.construct(
                        uri, item_constraint)

        props['__itemtype__'] = item_constraint

        props.update(addl_constraints)

        validator = type(str(name), (ArrayWrapper,), props)

        return validator
