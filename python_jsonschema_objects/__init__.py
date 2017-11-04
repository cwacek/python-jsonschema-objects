import jsonschema
from jsonschema import Draft4Validator
from jsonschema.compat import iteritems
import json
import codecs
import copy
import os.path
import inflection
import six

import logging
logger = logging.getLogger(__name__)


import python_jsonschema_objects.classbuilder as classbuilder
from python_jsonschema_objects.validators import ValidationError
import python_jsonschema_objects.util
import python_jsonschema_objects.markdown_support

__all__ = ['ObjectBuilder', 'markdown_support', 'ValidationError']

FILE = __file__

class ObjectBuilder(object):

    def __init__(self, schema_uri, resolved={}):
        self.mem_resolved = resolved

        if isinstance(schema_uri, six.string_types):
            uri = os.path.normpath(schema_uri)
            self.basedir = os.path.dirname(uri)
            with codecs.open(uri, 'r', 'utf-8') as fin:
                self.schema = json.loads(fin.read())
        else:
            self.schema = schema_uri
            uri = os.path.normpath(FILE)
            self.basedir = os.path.dirname(uri)

        self.resolver = jsonschema.RefResolver.from_schema(
            self.schema,
            handlers={
                'file': self.relative_file_resolver,
                'memory': self.memory_resolver
            }
        )

        meta_validator = Draft4Validator(Draft4Validator.META_SCHEMA)
        meta_validator.validate(self.schema)
        self.validator = Draft4Validator(self.schema,
                                         resolver=self.resolver)


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
        setattr(self, '_schema', val)

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
        with codecs.open(path, 'r', 'utf-8') as fin:
            result = json.loads(fin.read())
        return result

    def validate(self, obj):
        try:
            return self.validator.validate(obj)
        except jsonschema.ValidationError as e:
            raise ValidationError(e)


    def build_classes(self,strict=False):
        """

        Args:
            strict: use this to validate required fields while creating the class

        Returns:

        """
        kw = {"strict": strict}
        builder = classbuilder.ClassBuilder(self.resolver)
        for nm, defn in iteritems(self.schema.get('definitions', {})):
            uri = util.resolve_ref_uri(
                self.resolver.resolution_scope,
                "#/definitions/" + nm)
            builder.construct(uri, defn, **kw)

        nm = self.schema['title'] if 'title' in self.schema else self.schema['id']
        nm = inflection.parameterize(six.text_type(nm), '_')

        builder.construct(nm, self.schema,**kw)
        self._resolved = builder.resolved

        return (
            util.Namespace.from_mapping(dict(
                (inflection.camelize(uri.split('/')[-1]),
                 klass) for uri,
                klass in six.iteritems(builder.resolved)))
        )


if __name__ == '__main__':

    validator = ObjectBuilder("../../protocol/json/schema.json")

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
