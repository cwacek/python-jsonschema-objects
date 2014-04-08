import python_jsonschema_objects.util as util
import python_jsonschema_objects.validators as validators

import six


class ProtocolBase(object):
    __propinfo__ = {}
    __required__ = set()

    __SCHEMA_TYPES__ = {
        'array': list,
        'boolean': bool,
        'integer': int,
        'number': float,
        'null': None,
        'string': six.text_type,
        'object': dict
    }

    def __str__(self):
        return repr(self)

    def __repr__(self):
        props = ["%s=%s" % (k, str(v)) for k, v in
                 self._properties.iteritems()]
        return "<%s %s>" % (
            self.__class__.__name__,
            " ".join(props)
        )

    def __init__(this, **props):
        this._properties = dict(zip(this.__prop_names__.keys(),
                                    [None for x in
                                     xrange(len(this.__prop_names__))]))

        for prop in props:
            try:
                propname = this.__prop_names__[prop]
            except KeyError:
                raise AttributeError(
                    "{0} is not valid property "
                    "of '{1}'".format(prop,
                                      this.__class__))

            setattr(this, propname, props[prop])

        if len(props) > 0:
            this.validate()

    @classmethod
    def propinfo(cls, propname):
        if propname not in cls.__propinfo__:
            return {}
        return cls.__propinfo__[propname]

    def serialize(self):
        self.validate()
        enc = util.ProtocolJSONEncoder()
        return enc.encode(self)

    def validate(this):
        missing = [x for x in this.__required__
                   if this._properties[x] is None]

        if len(missing) > 0:
            raise validators.ValidationError(
                "'{0}' are required attributes for {1}"
                            .format(missing, this.__class__))

        for prop, val in this._properties.iteritems():
            if val is None:
                continue

            this.validate_property(prop, val)

        return True

    def validate_property(self, prop, val):
        """Validate a property value, and return true or false

        :propinfo: A dictionary containing property info
        :propval: The property value
        :returns: True or False
        """
        info = self.propinfo(prop)

        for param, paramval in info.iteritems():
            validator = getattr(validators, param, None)
            if validator is not None:
                if param == 'minimum':
                    validator(paramval, val,
                              info.get('exclusiveMinimum',
                                       False))
                elif param == 'maximum':
                    validator(paramval, val,
                              info.get('exclusiveMaximum',
                                       False))
                else:
                    validator(paramval, val)


class ClassBuilder(object):

    def __init__(self, resolver):
        self.resolver = resolver
        self.resolved = {}

    def resolve_classes(self, iterable):
        pp = []
        for elem in iterable:
            if '$ref' in elem:
                ref = elem['$ref']
                uri = util.resolve_ref_uri(self.resolver.resolution_scope, ref)
                if uri in self.resolved:
                    pp.append(self.resolved[uri])
                else:
                    with self.resolver.resolving(ref) as resolved:
                        self.resolved[uri] = self.construct(
                            uri,
                            resolved,
                            (ProtocolBase,))
                        pp.append(self.resolved[uri])
            else:
                pp.append(elem)

        return pp

    def construct(self, uri, clsdata, parent=(ProtocolBase,)):
        if 'oneOf' in clsdata:
            potential_parents = self.resolve_classes(clsdata['oneOf'])

            for p in potential_parents:
                if issubclass(p, ProtocolBase):
                    self.resolved[uri] = self._build_object(
                        uri,
                        clsdata,
                        (p,))
                else:
                    raise Exception("Don't know how to deal with this")

        elif 'anyOf' in clsdata:
            raise NotImplementedError(
                "anyOf is not supported as bare property")

        elif 'allOf' in clsdata:
            potential_parents = self.resolve_classes(clsdata['allOf'])
            parents = []
            for p in potential_parents:
                if isinstance(p, dict):
                    # This is additional constraints
                    clsdata.update(p)
                elif issubclass(p, ProtocolBase):
                    parents.append(p)

            self.resolved[uri] = self._build_object(
                uri,
                clsdata,
                parents)
            return self.resolved[uri]

        elif '$ref' in clsdata:

            if uri in self.resolved:
                return self.resolved[uri]
            else:
                reffed_doc = self.resolver.resolve_remote(uri)
                self.resolved[uri] = self._build_object(
                    uri,
                    reffed_doc,
                    parent)
                return self.resolved[uri]

        elif 'array' in clsdata and 'items' in clsdata:
            self.resolved[uri] = self._build_object(
                uri,
                clsdata,
                parent)

        elif (clsdata.get('type', None) == 'object' or
              clsdata.get('properties', None) is not None):
            self.resolved[uri] = self._build_object(
                uri,
                clsdata,
                parent)
            return self.resolved[uri]
        else:
            raise NotImplementedError(
                "Unable to parse schema object with "
                "no type and no reference")

    def _build_object(self, nm, clsdata, parents):

        props = {}

        properties = {}
        for p in parents:
            properties = util.propmerge(properties, p.__propinfo__)

        if 'properties' in clsdata:
            properties = util.propmerge(properties, clsdata['properties'])

        name_translation = {}

        for prop, detail in properties.items():
            properties[prop]['raw_name'] = prop
            name_translation[prop] = prop.replace('@', '')
            prop = name_translation[prop]

            if 'type' not in detail and '$ref' in detail:
                ref = detail['$ref']
                uri = util.resolve_ref_uri(self.resolver.resolution_scope, ref)
                if uri in self.resolved:
                    props[prop] = make_property(prop,
                                                {'type': self.resolved[uri]},
                                                self.resolved[uri].__doc__)
                    properties[prop]['$ref'] = uri
                    properties[prop]['type'] = self.resolved[uri]
                else:
                    with self.resolver.resolving(ref) as resolved:
                        self.resolved[uri] = self.construct(
                            uri,
                            resolved,
                            (ProtocolBase,))
            elif 'oneOf' in detail:
                potential = self.resolve_classes(detail['oneOf'])
                desc = detail[
                    'description'] if 'description' in detail else ""
                props[prop] = make_property(prop,
                                            {'type': potential}, desc
                                            )

            elif 'type' in detail and detail['type'] == 'array':
                if 'items' in detail and isinstance(detail['items'], dict):
                    if '$ref' in detail['items']:
                        uri = util.resolve_ref_uri(
                            self.resolver.resolution_scope,
                            detail['items']['$ref'])
                        typ = self.construct(uri, detail['items'])
                        propdata = {
                            'type': 'array',
                            'validator': validators.ArrayValidator.create(
                                uri,
                                item_constraint=typ)}
                    else:
                        uri = "{0}/{1}_{2}".format(nm,
                                                   prop, "<anonymous_field>")
                        try:
                            typ = self.construct(uri, detail['items'])
                            propdata = {'type': 'array',
                                        'validator': validators.ArrayValidator.create(uri, item_constraint=typ,
                                                                                addl_constraints=detail)}
                        except NotImplementedError:
                            typ = detail['items']
                            propdata = {'type': 'array',
                                        'validator': validators.ArrayValidator.create(uri,
                                                                                item_constraint=typ,
                                                                                addl_constraints=detail)}

                    props[prop] = make_property(prop,
                                                propdata,
                                                typ.__doc__)
                elif 'items' in detail:
                    typs = []
                    for i, elem in enumerate(detail['items']):
                        uri = "{0}/{1}/<anonymous_{2}>".format(nm, prop, i)
                        typ = self.construct(uri, detail['items'])
                        typs.append(typ)

                    props[prop] = make_property(prop,
                                                {'type': 'tuple',
                                                 'items': typ},
                                                typ.__doc__)

            else:
                desc = detail[
                    'description'] if 'description' in detail else ""

                props[prop] = make_property(prop, detail, desc)

        """ If this object itself has a 'oneOf' designation, then
        make the validation 'type' the list of potential objects.
        """
        if 'oneOf' in clsdata:
            klasses = self.resolve_classes(clsdata['oneOf'])
            # Need a validation to check that it meets one of them
            props['__validation__'] = {'type': klasses}

        props['__prop_names__'] = name_translation

        props['__propinfo__'] = properties
        required = set.union(*[p.__required__ for p in parents])

        if 'required' in clsdata:
            for prop in clsdata['required']:
                required.add(prop.replace('@', ''))

        props['__required__'] = required

        cls = type(str(nm.split('/')[-1]), tuple(parents), props)

        return cls


def make_property(prop, info, desc=""):

    def getprop(this):
        try:
            return this._properties[prop]
        except KeyError:
            raise AttributeError("No such attribute")

    def setprop(this, val):
        if isinstance(info['type'], (list, tuple)):
            ok = False
            for typ in info['type']:
                if isinstance(val, typ):
                    ok = True
                    break
                elif not isinstance(val, ProtocolBase):
                    errors = []
                    try:
                        val = typ(**val)
                    except Exception as e:
                        errors.append(
                            "Failed to coerce to '{0}': {1}".format(typ, e))
                        pass
                    else:
                        val.validate()
                        ok = True
                        break

            if not ok:
                errstr = "\n".join(errors)
                raise TypeError(
                    "Value must be one of {0}: \n{1}".format(info['type'], errstr))

        elif info['type'] == 'array':
            instance = info['validator'](val)
            instance.validate()

        elif (info['type'] in this.__SCHEMA_TYPES__.keys() and val is not None):
            val = this.__SCHEMA_TYPES__[info['type']](val)

        elif issubclass(info['type'], ProtocolBase):
            if not isinstance(val, info['type']):
                val = info['type'](**val)

            val.validate()

        this.validate_property(prop, val)
        this._properties[prop] = val

    def delprop(this):
        if prop in this.__required__:
            raise AttributeError("'%s' is required" % prop)
        else:
            del this._properties[prop]

    return property(getprop, setprop, delprop, desc)
