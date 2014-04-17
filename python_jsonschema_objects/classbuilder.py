import python_jsonschema_objects.util as util
import python_jsonschema_objects.validators as validators

import collections
import itertools
import six


class ProtocolBase( collections.MutableMapping):
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

    def as_dict(self):
      out = {}
      for prop in self:
          propval = getattr(self, prop)
          proptype = self.__propinfo__[prop]['type']

          if proptype == 'array':
              out[prop] = [x.as_dict() for x in propval]
          elif proptype == 'object':
              out[prop] = propval.as_dict() if propval is not None else {}
          elif propval is not None:
              out[prop] = propval.as_dict()

      return out

    def __str__(self):
        return repr(self)

    def __repr__(self):
        props = ["%s=%s" % (k, str(v)) for k, v in
                 itertools.chain(self._properties.iteritems(),
                                 self._extended_properties.iteritems())]
        return "<%s %s>" % (
            self.__class__.__name__,
            " ".join(props)
        )

    def __init__(this, **props):
        this._extended_properties = dict()
        this._properties = dict(zip(this.__prop_names__.keys(),
                                    [None for x in
                                     xrange(len(this.__prop_names__))]))

        for prop in props:
            try:
                propname = this.__prop_names__[prop]
            except KeyError:
                propname = prop

            setattr(this, propname, props[prop])

        if len(props) > 0:
            this.validate()

    def __setattr__(self, name, val):
      if name.startswith("_"):
        object.__setattr__(self, name, val)
      elif name in self.__propinfo__:
        # If its in __propinfo__, then it actually has a property defined.
        # The property does special validation, so we actually need to
        # run its setter. We get it from the class definition and call
        # it directly. XXX Heinous.
        prop = self.__class__.__dict__[name]
        prop.fset(self, val)
      else:
        # This is an additional property of some kind
        if getattr(self, '__extensible__', None) is False:
          raise validators.ValidationError(
              "Attempted to set unknown property '{0}', but 'additionalProperties' is false.")
        else:
          typ = getattr(self, '__extensible__', None)
          if isinstance(typ, type) and issubclass(typ, LiteralValue):
            val = typ(val)
          elif isinstance(typ, type) and issubclass(typ, ProtocolBase):
            val = typ(**val)

        self._extended_properties[name] = val

    """ Implement collections.MutableMapping methods """

    def __iter__(self):
      import itertools
      return itertools.chain(self._extended_properties.iterkeys(),
                             self._properties.iterkeys())

    def __len__(self):
      return len(self._extended_properties) + len(self._properties)

    def __getitem__(self, key):
      return self.__getattr__(key)

    def __setitem__(self, key, val):
      return self.__setattr__(key, val)

    def __delitem__(self, key):
      return self.__delattr__(key)

    def __getattr__(self, name):
      if name not in self._extended_properties:
        raise AttributeError("{0} is not a valid property of {1}".format(
          name, self.__class__.__name__))

      return self._extended_properties[name]

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
                   if x not in this._properties or this._properties[x] is None]

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


class LiteralValue(ProtocolBase):
  """Docstring for LiteralValue """

  def __init__(self, value):
      """@todo: to be defined

      :value: @todo

      """
      self._value = value
      self.validate()

  def as_dict(self):
      return self._value

  def __repr__(self):
      return "<%s %s>" % (
          self.__class__.__name__,
          str(self._value)
      )

  def validate(self):
      self.validate_property('__literal__', self._value)

  def __int__(self):
    return int(self._value)

  def __float__(self):
    return float(self._value)

  def __str__(self):
    return str(self._value)


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
                with self.resolver.resolving(uri) as resolved:
                    self.resolved[uri] = self._build_object(
                        uri,
                        resolved,
                        parent)
                return self.resolved[uri]

        elif 'array' in clsdata and 'items' in clsdata:
            self.resolved[uri] = self._build_object(
                uri,
                clsdata,
                parent)

        elif (clsdata.get('type', None) == 'object' or
              clsdata.get('properties', None) is not None or
              clsdata.get('additionalProperties', None is not None)):
            self.resolved[uri] = self._build_object(
                uri,
                clsdata,
                parent)
            return self.resolved[uri]
        elif clsdata.get('type') in ('integer', 'number', 'string', 'boolean'):
            self.resolved[uri] = self._build_literal(
                uri,
                clsdata)
            return self.resolved[uri]
        else:
            raise NotImplementedError(
                "Unable to parse schema object with "
                "no type and no reference")

    def _build_literal(self, nm, clsdata):
      """@todo: Docstring for _build_literal

      :nm: @todo
      :clsdata: @todo
      :returns: @todo

      """
      cls = type(str(nm), tuple((LiteralValue,)), {
        '__propinfo__': { '__literal__': clsdata}
        })

      return cls

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

            if detail.get('type', None) == 'object':
                uri = "{0}/{1}_{2}".format(nm,
                                           prop, "<anonymous>")
                self.resolved[uri] = self.construct(
                    uri,
                    detail,
                    (ProtocolBase,))

                props[prop] = make_property(prop,
                    {'type': self.resolved[uri]},
                      self.resolved[uri].__doc__)
                properties[prop]['type'] = self.resolved[uri]

            elif 'type' not in detail and '$ref' in detail:
                ref = detail['$ref']
                uri = util.resolve_ref_uri(self.resolver.resolution_scope, ref)
                if uri not in self.resolved:
                    with self.resolver.resolving(ref) as resolved:
                        self.resolved[uri] = self.construct(
                            uri,
                            resolved,
                            (ProtocolBase,))

                props[prop] = make_property(prop,
                                            {'type': self.resolved[uri]},
                                            self.resolved[uri].__doc__)
                properties[prop]['$ref'] = uri
                properties[prop]['type'] = self.resolved[uri]

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
                uri = "{0}/{1}".format(nm, prop)
                typ = self.construct(uri, detail)

                props[prop] = make_property(prop, {'type': typ}, desc)

        """ If this object itself has a 'oneOf' designation, then
        make the validation 'type' the list of potential objects.
        """
        if 'oneOf' in clsdata:
            klasses = self.resolve_classes(clsdata['oneOf'])
            # Need a validation to check that it meets one of them
            props['__validation__'] = {'type': klasses}

        props['__extensible__'] = True
        if 'additionalProperties' in clsdata:
          addlProp = clsdata['additionalProperties']

          if addlProp is False:
            props['__extensible__'] = False
          else:
            if '$ref' in addlProp:
                refs = self.resolve_classes([addlProp])
            else:
                uri = "{0}/{1}_{2}".format(nm,
                                           "<additionalProperties>", "<anonymous>")
                self.resolved[uri] = self.construct(
                    uri,
                    addlProp,
                    (ProtocolBase,))
                refs = [self.resolved[uri]]

            props['__extensible__'] = refs[0]


        props['__prop_names__'] = name_translation

        props['__propinfo__'] = properties
        required = set.union(*[p.__required__ for p in parents])

        if 'required' in clsdata:
            for prop in clsdata['required']:
                required.add(prop.replace('@', ''))

        invalid_requires = [req for req in required if req not in props['__propinfo__']]
        if len(invalid_requires) > 0:
          raise validators.ValidationError("Schema Definition Error: {0} schema requires "
                                           "'{1}', but properties are not defined"
                                           .format(nm, invalid_requires))

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
                    "Object must be one of {0}: \n{1}".format(info['type'], errstr))

        elif info['type'] == 'array':
            instance = info['validator'](val)
            val = instance.validate()

        elif (info['type'] in this.__SCHEMA_TYPES__.keys() and val is not None):
            val = this.__SCHEMA_TYPES__[info['type']](val)

        elif issubclass(info['type'], LiteralValue):
            if not isinstance(val, info['type']):
                val = info['type'](val)

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
