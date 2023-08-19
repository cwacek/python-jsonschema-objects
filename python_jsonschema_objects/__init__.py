__all__ = ["ObjectBuilder", "markdown_support", "ValidationError"]

import codecs
import copy
import json
import logging
import os.path
import warnings

import inflection
import jsonschema
import six
from jsonschema import Draft4Validator

from python_jsonschema_objects import classbuilder, markdown_support, util
from python_jsonschema_objects.validators import ValidationError

logger = logging.getLogger(__name__)

FILE = __file__

SUPPORTED_VERSIONS = (
    "http://json-schema.org/draft-03/schema#",
    "http://json-schema.org/draft-04/schema#",
)


class ObjectBuilder(object):
    def __init__(self, schema_uri, resolved={}, resolver=None, validatorClass=None):
        self.mem_resolved = resolved

        if isinstance(schema_uri, six.string_types):
            uri = os.path.normpath(schema_uri)
            self.basedir = os.path.dirname(uri)
            with codecs.open(uri, "r", "utf-8") as fin:
                self.schema = json.loads(fin.read())
        else:
            self.schema = schema_uri
            uri = os.path.normpath(FILE)
            self.basedir = os.path.dirname(uri)

        if (
            "$schema" in self.schema
            and self.schema["$schema"] not in SUPPORTED_VERSIONS
        ):
            warnings.warn(
                "Schema version {} not recognized. Some "
                "keywords and features may not be supported.".format(
                    self.schema["$schema"]
                )
            )

        self.resolver = resolver or jsonschema.RefResolver.from_schema(self.schema)
        self.resolver.handlers.update(
            {"file": self.relative_file_resolver, "memory": self.memory_resolver}
        )

        validatorClass = validatorClass or Draft4Validator
        meta_validator = validatorClass(validatorClass.META_SCHEMA)
        meta_validator.validate(self.schema)
        self.validator = validatorClass(self.schema, resolver=self.resolver)

        self._classes = None
        self._resolved = None

    @property
    def schema(self):
        try:
            return copy.deepcopy(self._schema)
        except AttributeError:
            raise ValidationError("No schema provided")

    @schema.setter
    def schema(self, val):
        setattr(self, "_schema", val)

    @property
    def classes(self):
        if self._classes is None:
            self._classes = self.build_classes()
        return self._classes

    def get_class(self, uri):
        if self._resolved is None:
            self._classes = self.build_classes()
        return self._resolved.get(uri, None)

    def memory_resolver(self, uri):
        return self.mem_resolved[uri[7:]]

    def relative_file_resolver(self, uri):
        path = os.path.join(self.basedir, uri[8:])
        with codecs.open(path, "r", "utf-8") as fin:
            result = json.loads(fin.read())
        return result

    def validate(self, obj):
        try:
            return self.validator.validate(obj)
        except jsonschema.ValidationError as e:
            raise ValidationError(e)

    def build_classes(self, strict=False, named_only=False, standardize_names=True):
        """
        Build all of the classes named in the JSONSchema.

        Class names will be transformed using inflection by default, so names
        with spaces in the schema will be camelcased, while names without
        spaces will have internal capitalization dropped. Thus "Home Address"
        becomes "HomeAddress", while "HomeAddress" becomes "Homeaddress". To
        disable this behavior, pass standardize_names=False, but be aware that
        accessing names with spaces from the namespace can be problematic.

        Args:
            strict: (bool) use this to validate required fields while creating the class
            named_only: (bool) If true, only properties with an actual title attribute
                will be included in the resulting namespace (although all will be
                generated).
            standardize_names: (bool) If true (the default), class names will be
                transformed by camel casing

        Returns:
            A namespace containing all the generated classes

        """
        kw = {"strict": strict}
        builder = classbuilder.ClassBuilder(self.resolver)
        for nm, defn in six.iteritems(self.schema.get("definitions", {})):
            uri = util.resolve_ref_uri(
                self.resolver.resolution_scope, "#/definitions/" + nm
            )
            builder.construct(uri, defn, **kw)

        if standardize_names:
            name_transform = lambda t: inflection.camelize(
                inflection.parameterize(six.text_type(t), "_")
            )
        else:
            name_transform = lambda t: t

        nm = self.schema["title"] if "title" in self.schema else self.schema["$id"]
        nm = inflection.parameterize(six.text_type(nm), "_")

        builder.construct(nm, self.schema, **kw)
        self._resolved = builder.resolved

        classes = {}
        for uri, klass in six.iteritems(builder.resolved):
            title = getattr(klass, "__title__", None)
            if title is not None:
                classes[name_transform(title)] = klass
            elif not named_only:
                classes[name_transform(uri.split("/")[-1])] = klass

        return util.Namespace.from_mapping(classes)


if __name__ == "__main__":
    validator = ObjectBuilder("../../protocol/json/schema.json")

from . import _version

__version__ = _version.get_versions()["version"]
