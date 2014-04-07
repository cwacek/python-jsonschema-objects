class ValidationError(Exception):
    pass


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
        try:
          value = param(value)
        except:
            raise ValidationError(
                "{0} was not an instance of {1}".format(value, param))


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
