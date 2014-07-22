class ValidationError(Exception):
    pass

klassType = type


def multipleOf(param, value):
    quot, rem = divmod(value, param)
    if rem != 0:
        raise ValidationError(
            "{0} was not a multiple of {1}".format(value,
                                                   param))


def type(param, value):
    import classbuilder
    if isinstance(param, basestring):
        param = classbuilder.ProtocolBase.__SCHEMA_TYPES__[param]
    if not isinstance(value, param):
        raise ValidationError(
            "'{0}' was not an instance of {1}".format(value, param))


def enum(param, value):
    if value not in param:
        raise ValidationError(
            "{0} was not one of {1}".format(value, param))


def minimum(param, value, exclusive):
    if exclusive:
        if value < param:
            raise ValidationError(
                "{0} was less than {1}".format(value, param))
    else:
        if value <= param:
            raise ValidationError(
                "{0} was less or equal to than {1}".format(value, param))


def maximum(param, value, exclusive):
    return minimum(value, param, not exclusive)


def maxLength(param, value):
    if len(value) > param:
        raise ValidationError(
            "{0} was longer than {1} characters".format(value, param))


def minLength(param, value):
    if len(value) < param:
        raise ValidationError(
            "{0} was fewer than {1} characters".format(value, param))


def pattern(param, value):
    import re
    match = re.search(param, value)
    if not match:
        raise ValidationError(
            "{0} did not match {1}".format(value, param)
        )


class ArrayValidator(object):

    def __init__(self, ary):
        self.data = ary

    def validate(self):
        converted = self.validate_items()
        self.validate_length()
        self.validate_uniqueness()
        return converted

    def validate_uniqueness(self):
        import classbuilder
        import validators

        if getattr(self, 'uniqueItems', None) is not None:
            testset = set(self.data)
            if len(testset) != len(self.data):
                raise validators.ValidationError(
                    "{0} had duplicate elements, but uniqueness required"
                    .format(self.data))

    def validate_length(self):
        import classbuilder
        import validators

        if getattr(self, 'minItems', None) is not None:
            if len(self.data) < self.minItems:
                raise validators.ValidationError(
                    "{1} has too few elements. Wanted {0}."
                    .format(self.minItems, self.data))

        if getattr(self, 'maxItems', None) is not None:
            if len(self.data) > self.maxItems:
                raise validators.ValidationError(
                    "{1} has too few elements. Wanted {0}."
                    .format(self.maxItems, self.data))

    def validate_items(self):
        import classbuilder
        import validators

        if self.__itemtype__ is None:
            return

        if not isinstance(self.__itemtype__, (tuple, list)):
            self.__itemtype__ = [
                self.__itemtype__ for x in xrange(len(self.data))]

        if len(self.__itemtype__) > len(self.data):
            raise validators.ValidationError(
                "{1} does not have sufficient elements to validate against {0}"
                .format(self.__itemtype__, self.data))

        typed_elems = []
        for i, elem in enumerate(self.data):
            try:
                typ = self.__itemtype__[i]
            except IndexError:
                # It's actually permissible to run over a tuple constraint.
                pass

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

            elif issubclass(typ, classbuilder.LiteralValue):
                val = typ(elem)
                val.validate()
                typed_elems.append(val)
            elif issubclass(typ, classbuilder.ProtocolBase):
                try:
                  val = typ(**elem)
                except TypeError:
                  raise ValidationError("'{0}' was not a valid value for '{1}'".format(elem, typ))
                val.validate()
                typed_elems.append(val)
            elif issubclass(typ, ArrayValidator):
                val = typ(elem)
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
        import classbuilder
        props = {}

        if item_constraint is not None:
            if isinstance(item_constraint, (tuple, list)):
                for i, elem in enumerate(item_constraint):
                    isdict = isinstance(elem, (dict,))
                    isklass = isinstance( elem, klassType) and issubclass(
                        elem, (classbuilder.ProtocolBase, classbuilder.LiteralValue))

                    if not any([isdict, isklass]):
                        raise TypeError(
                            "Item constraint (position {0}) was not a schema".format(i))
            else:
                isdict = isinstance(item_constraint, (dict,))
                isklass = isinstance( item_constraint, klassType) and issubclass(
                    item_constraint, (classbuilder.ProtocolBase, classbuilder.LiteralValue))

                if not any([isdict, isklass]):
                    raise TypeError("Item constraint was not a schema")

                if isdict and item_constraint['type'] == 'array':
                    item_constraint = ArrayValidator.create(name + "#sub",
                                                            item_constraint=item_constraint[
                                                                'items'],
                                                            addl_constraints=item_constraint)

        props['__itemtype__'] = item_constraint

        props.update(addl_constraints)

        validator = klassType(str(name), (ArrayValidator,), props)

        return validator

