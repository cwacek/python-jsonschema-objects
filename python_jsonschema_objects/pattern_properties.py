import six
import re
import python_jsonschema_objects.validators as validators
import python_jsonschema_objects.util as util
from python_jsonschema_objects.literals import MakeLiteral

import collections

import logging

import python_jsonschema_objects.wrapper_types

logger = logging.getLogger(__name__)

PatternDef = collections.namedtuple("PatternDef", "pattern schema_type")


class ExtensibleValidator(object):
    def __init__(self, name, schemadef, builder):
        import python_jsonschema_objects.classbuilder as cb

        self._pattern_types = []
        self._additional_type = True

        addlProp = schemadef.get("additionalProperties", True)

        if addlProp is False:
            self._additional_type = False
        elif addlProp is True:
            self._additional_type = True
        else:
            if "$ref" in addlProp:
                refs = builder.resolve_classes([addlProp])
            else:
                uri = "{0}/{1}_{2}".format(
                    name, "<additionalProperties>", "<anonymous>"
                )
                builder.resolved[uri] = builder.construct(
                    uri, addlProp, (cb.ProtocolBase,)
                )
                refs = [builder.resolved[uri]]

            self._additional_type = refs[0]

        for pattern, typedef in six.iteritems(schemadef.get("patternProperties", {})):
            if "$ref" in typedef:
                refs = builder.resolve_classes([typedef])
            else:
                uri = "{0}/{1}_{2}".format(name, "<patternProperties>", pattern)

                builder.resolved[uri] = builder.construct(
                    uri, typedef, (cb.ProtocolBase,)
                )
                refs = [builder.resolved[uri]]

            self._pattern_types.append(
                PatternDef(pattern=re.compile(pattern), schema_type=refs[0])
            )

    def _make_type(self, typ, val):
        import python_jsonschema_objects.classbuilder as cb

        if getattr(typ, "isLiteralClass", None) is True:
            return typ(val)

        if util.safe_issubclass(typ, cb.ProtocolBase):
            return typ(**util.coerce_for_expansion(val))

        if util.safe_issubclass(
            typ, python_jsonschema_objects.wrapper_types.ArrayWrapper
        ):
            return typ(val)

        raise validators.ValidationError(
            "additionalProperty type {0} was neither a literal "
            "nor a schema wrapper: {1}".format(typ, val)
        )

    def instantiate(self, name, val):
        import python_jsonschema_objects.classbuilder as cb

        for p in self._pattern_types:
            if p.pattern.search(name):
                logger.debug(
                    "Found patternProperties match: %s %s" % (p.pattern.pattern, name)
                )
                return self._make_type(p.schema_type, val)

        if self._additional_type is True:

            valtype = [
                k
                for k, t in validators.SCHEMA_TYPE_MAPPING
                if t is not None and isinstance(val, t)
            ]
            valtype = valtype[0]
            return MakeLiteral(name, valtype, val)

        elif isinstance(self._additional_type, type):
            return self._make_type(self._additional_type, val)

        raise validators.ValidationError(
            "additionalProperties not permitted " "and no patternProperties specified"
        )
