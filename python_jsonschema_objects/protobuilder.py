import jsonschema
from jsonschema import Draft4Validator
from jsonschema.compat import iteritems
import json
import codecs
import os.path
import inflection

import classbuilder
import util


class Validator(object):

    def __init__(self, schema_uri):
        uri = os.path.normpath(schema_uri)
        self.basedir = os.path.dirname(uri)
        with open(uri) as fin:
            self.schema = json.loads(fin.read())

        self.resolver = jsonschema.RefResolver.from_schema(
            self.schema,
            handlers={
                'file': self.relative_file_resolver
            }
        )

        self.validator = Draft4Validator(self.schema,
                                         resolver=self.resolver)

    def relative_file_resolver(self, uri):
        path = os.path.join(self.basedir, uri[8:])
        with codecs.open(path, 'r', 'utf-8') as fin:
            result = json.loads(fin.read())
        return result

    def validate(self, obj):
        return self.validator.is_valid(obj)

    def build_classes(self):
        builder = classbuilder.ClassBuilder(self.resolver)
        for k, v in iteritems(self.schema):
            if k == 'definitions':
                for nm, defn in iteritems(v):
                    uri = util.resolve_ref_uri(
                        self.resolver.resolution_scope,
                        "#/definitions/" + nm)
                    builder.construct(uri, defn)

        nm = self.schema['title'] if 'title' in self.schema else self.schema['id']

        builder.construct(nm, self.schema)

        return (
            util.Namespace.from_mapping(dict(
                (inflection.camelize(uri.split('/')[-1]),
                 klass) for uri,
                klass in builder.resolved.iteritems()))
        )


if __name__ == '__main__':

    validator = Validator("../../protocol/json/schema.json")
