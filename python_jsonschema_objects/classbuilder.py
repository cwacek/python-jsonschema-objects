import python_jsonschema_objects.util as util
import python_jsonschema_objects.validators as validators

import collections
import itertools
import six
import sys

import logging
logger = logging.getLogger(__name__)



# Long is no longer a thing in python3.x
if sys.version_info > (3,):
  long = int

class ProtocolBase(collections.MutableMapping):
    """ An instance of a class generated from the provided
    schema. All properties will be validated according to
    the definitions provided. However, whether or not all required
    properties have been provide will *not* be validated.

    Args:
        **props: Properties with which to populate the class object

    Returns:
        The class object populated with values

    Raises:
        validators.ValidationError: If any of the provided properties
            do not pass validation
    """
    __propinfo__ = {}
    __required__ = set()

    __SCHEMA_TYPES__ = {
        'array': list,
        'boolean': bool,
        'integer': int,
        'number': (float, int, long),
        'null': None,
        'string': six.string_types,
        'object': dict
    }

    def as_dict(self):
        """ Return a dictionary containing the current values
        of the object.

        Returns:
            (dict): The object represented as a dictionary
        """
        out = {}
        for prop in self:
            propval = getattr(self, prop)

            if isinstance(propval, list):
                out[prop] = [getattr(x, 'as_dict', lambda :x)() for x in propval]
            elif isinstance(propval, (ProtocolBase, LiteralValue)):
                out[prop] = propval.as_dict()
            elif propval is not None:
                out[prop] = propval

        return out

    def for_json(self):
        return self.as_dict()

    def __eq__(self, other):
        return self.as_dict() == other.as_dict()

    def __str__(self):
        inverter = dict((v, k) for k,v in six.iteritems(self.__prop_names__))
        props = ["%s" % (inverter.get(k, k),) for k, v in
                 itertools.chain(six.iteritems(self._properties),
                                 six.iteritems(self._extended_properties))]
        return "<%s attributes: %s>" % (self.__class__.__name__, ", ".join(props))

    def __repr__(self):
        inverter = dict((v, k) for k,v in six.iteritems(self.__prop_names__))
        props = ["%s=%s" % (inverter.get(k, k), str(v)) for k, v in
                 itertools.chain(six.iteritems(self._properties),
                                 six.iteritems(self._extended_properties))]
        return "<%s %s>" % (
            self.__class__.__name__,
            " ".join(props)
        )

    @classmethod
    def from_json(cls, jsonmsg):
        """ Create an object directly from a JSON string.

        Applies general validation after creating the
        object to check whether all required fields are
        present.

        Args:
            jsonmsg (str): An object encoded as a JSON string

        Returns:
            An object of the generated type

        Raises:
            ValidationError: if `jsonmsg` does not match the schema
                `cls` was generated from
        """
        import json
        msg = json.loads(jsonmsg)
        obj = cls(**msg)
        obj.validate()
        return obj

    def __new__(cls, **props):
        """ Overridden to support oneOf, where we need to
        instantiate a different class depending on what
        value we've seen """
        if getattr(cls, '__validation__', None) is None:
            new = super(ProtocolBase, cls).__new__
            if new is object.__new__:
                return new(cls)
            return new(cls, **props)

        valid_types = cls.__validation__.get('type', None)

        if valid_types is None or not isinstance(valid_types, list):
            new = super(ProtocolBase, cls).__new__
            if new is object.__new__:
                return new(cls)
            return new(cls, **props)

        obj = None
        validation_errors = []
        for klass in valid_types:
            logger.debug(util.lazy_format(
                "Attempting to instantiate {0} as {1}",
                cls, klass))
            try:
                obj = klass(**props)
            except validators.ValidationError as e:
                validation_errors.append((klass, e))
            else:
                break

        else:  # We got nothing
            raise validators.ValidationError(
                "Unable to instantiate any valid types: \n"
                "\n".join("{0}: {1}".format(k, e) for k, e in validation_errors)
            )

        return obj

    def __init__(self, **props):
        self._extended_properties = dict()
        self._properties = dict(zip(self.__prop_names__.values(),
                                    [None for x in
                                     six.moves.xrange(len(self.__prop_names__))]))

        for prop in props:

            try:
              logger.debug(util.lazy_format("Setting value for '{0}' to {1}", prop, props[prop]))
              setattr(self, prop, props[prop])
            except validators.ValidationError as e:
              import sys
              raise six.reraise(type(e), type(e)(str(e) + " \nwhile setting '{0}' in {1}".format(
                  prop, self.__class__.__name__)), sys.exc_info()[2])

        #if len(props) > 0:
        #    self.validate()

    def __setattr__(self, name, val):
        if name.startswith("_"):
            object.__setattr__(self, name, val)
        elif name in self.__propinfo__:
            # If its in __propinfo__, then it actually has a property defined.
            # The property does special validation, so we actually need to
            # run its setter. We get it from the class definition and call
            # it directly. XXX Heinous.
            prop = self.__class__.__dict__[self.__prop_names__[name]]
            prop.fset(self, val)
        else:
            # This is an additional property of some kind
            typ = getattr(self, '__extensible__', None)
            if typ is False:
                raise validators.ValidationError(
                    "Attempted to set unknown property '{0}', "
                    "but 'additionalProperties' is false.".format(name))
            if typ is True:
                # There is no type defined, so just make it a basic literal
                # Pick the type based on the type of the values
                valtype = [k for k, t in six.iteritems(self.__SCHEMA_TYPES__)
                           if t is not None and isinstance(val, t)]
                valtype = valtype[0]
                val = MakeLiteral(name, valtype, val)
            elif isinstance(typ, type) and getattr(typ, 'isLiteralClass', None) is True:
                val = typ(val)
            elif isinstance(typ, type) and util.safe_issubclass(typ, ProtocolBase):
                val = typ(**util.coerce_for_expansion(val))

            self._extended_properties[name] = val

    """ Implement collections.MutableMapping methods """

    def __iter__(self):
      import itertools
      return itertools.chain(six.iterkeys(self._extended_properties),
                             six.iterkeys(self._properties))

    def __len__(self):
      return len(self._extended_properties) + len(self._properties)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, val):
      return setattr(self,key, val)

    def __delitem__(self, key):
        if key in self._extended_properties:
            del self._extended_properties[key]
            return

        return delattr(self, key)

    def __getattr__(self, name):
        if name in self.__prop_names__:
            raise KeyError(name)
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

    def validate(self):
        """ Applies all defined validation to the current
        state of the object, and raises an error if 
        they are not all met.
        
        Raises:
            ValidationError: if validations do not pass
        """

        propname = lambda x: self.__prop_names__[x]
        missing = [x for x in self.__required__
                   if propname(x) not in self._properties
                   or self._properties[propname(x)] is None]

        if len(missing) > 0:
            raise validators.ValidationError(
                "'{0}' are required attributes for {1}"
                            .format(missing, self.__class__.__name__))

        for prop, val in six.iteritems(self._properties):
            if val is None:
                continue

            if isinstance(val, ProtocolBase):
                val.validate()
            elif getattr(val, 'isLiteralClass', None) is True:
                val.validate()
            elif isinstance(val, list):
                for subval in val:
                  subval.validate()
            else:
                # This object is of the wrong type, but just try setting it
                # The property setter will enforce its correctness
                # and handily coerce its type at the same time
                setattr(self, prop, val)

        return True

def MakeLiteral(name, typ, value, **properties):
      properties.update({'type': typ})
      klass =  type(str(name), tuple((LiteralValue,)), {
        '__propinfo__': { '__literal__': properties}
        })

      return klass(value)


class TypeProxy(object):

    def __init__(self, types):
        self._types = types

    def __call__(self, *a, **kw):
        validation_errors = []
        valid_types = self._types
        for klass in valid_types:
            logger.debug(util.lazy_format(
                "Attempting to instantiate {0} as {1}",
                self.__class__, klass))
            try:
                obj = klass(*a, **kw)
            except TypeError as e:
                validation_errors.append((klass, e))
            except validators.ValidationError as e:
                validation_errors.append((klass, e))
            else:
                return obj

        else:  # We got nothing
            raise validators.ValidationError(
                "Unable to instantiate any valid types: \n"
                "\n".join("{0}: {1}".format(k, e) for k, e in validation_errors)
            )


class LiteralValue(object):
  """Docstring for LiteralValue """

  isLiteralClass = True

  def __init__(self, value, typ=None):
      """@todo: to be defined

      :value: @todo

      """
      self._value = value
      self.validate()

  def as_dict(self):
      return self.for_json()

  def for_json(self):
      return self._value

  @classmethod
  def propinfo(cls, propname):
      if propname not in cls.__propinfo__:
          return {}
      return cls.__propinfo__[propname]

  def serialize(self):
      self.validate()
      enc = util.ProtocolJSONEncoder()
      return enc.encode(self)

  def __repr__(self):
      return "<%s %s>" % (
          self.__class__.__name__,
          str(self._value)
      )

  def validate(self):
      info = self.propinfo('__literal__')

      # this duplicates logic in validators.ArrayValidator.check_items; unify it.
      for param, paramval in sorted(six.iteritems(info), key=lambda x: x[0].lower() != 'type'):
          validator = validators.registry(param)
          if validator is not None:
              validator(paramval, self._value, info)


  def __cmp__(self, other):
    if isinstance(other, six.integer_types):
      return cmp(int(self), other)
    elif isinstance(other, six.string_types):
      return cmp(str(self), other)
    elif isinstance(other, float):
      return cmp(float(self), other)
    else:
      return cmp(id(self), id(other))

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

    def construct(self, uri, *args, **kw):
        """ Wrapper to debug things """
        logger.debug(util.lazy_format("Constructing {0}", uri))
        ret = self._construct(uri, *args, **kw)
        logger.debug(util.lazy_format("Constructed {0}", ret))
        return ret

    def _construct(self, uri, clsdata, parent=(ProtocolBase,)):

        if 'anyOf' in clsdata:
            raise NotImplementedError(
                "anyOf is not supported as bare property")

        elif 'allOf' in clsdata:
            potential_parents = self.resolve_classes(clsdata['allOf'])
            parents = []
            for p in potential_parents:
                if isinstance(p, dict):
                    # This is additional constraints
                    clsdata.update(p)
                elif util.safe_issubclass(p, ProtocolBase):
                    parents.append(p)

            self.resolved[uri] = self._build_object(
                uri,
                clsdata,
                parents)
            return self.resolved[uri]

        elif '$ref' in clsdata:

            if 'type' in clsdata and util.safe_issubclass(
                    clsdata['type'], (ProtocolBase, LiteralValue)):
                # It's possible that this reference was already resolved, in which
                # case it will have its type parameter set
                logger.debug(util.lazy_format("Using previously resolved type "
                              "(with different URI) for {0}", uri))
                self.resolved[uri] = clsdata['type']
            elif uri in self.resolved:
                logger.debug(util.lazy_format("Using previously resolved object for {0}", uri))
            else:
                logger.debug(util.lazy_format("Resolving object for {0}", uri))

                with self.resolver.resolving(uri) as resolved:
                    self.resolved[uri] = None # Set incase there is a circular reference in schema definition
                    self.resolved[uri] = self.construct(
                        uri,
                        resolved,
                        parent)

            return self.resolved[uri]

        elif clsdata.get('type') == 'array' and 'items' in clsdata:
            clsdata_copy = {}
            clsdata_copy.update(clsdata)
            self.resolved[uri] = validators.ArrayValidator.create(
                uri,
                item_constraint=clsdata_copy.pop('items'),
                classbuilder=self,
                **clsdata_copy)
            return self.resolved[uri]

        elif (clsdata.get('type', None) == 'object' or
              clsdata.get('properties', None) is not None or
              clsdata.get('additionalProperties', False)):
            self.resolved[uri] = self._build_object(
                uri,
                clsdata,
                parent)
            return self.resolved[uri]
        elif clsdata.get('type') in ('integer', 'number', 'string', 'boolean', 'null'):
            self.resolved[uri] = self._build_literal(
                uri,
                clsdata)
            return self.resolved[uri]
        elif 'enum' in clsdata:
            obj = self._build_literal(uri, clsdata)
            self.resolved[uri] = obj
            return obj

        elif 'type' in clsdata and util.safe_issubclass(clsdata['type'], ProtocolBase):
            self.resolved[uri] = clsdata.get('type')
            return self.resolved[uri]
        else:
            raise NotImplementedError(
                "Unable to parse schema object '{0}' with "
                "no type and no reference".format(clsdata))

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
        logger.debug(util.lazy_format("Building object {0}", nm))

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
                logger.debug(util.lazy_format("Designating {0} as oneOf {1}", prop, potential))
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
                            if 'oneOf' in detail['items']:
                                typ = TypeProxy([
                                    self.construct(uri + "_%s" % i, item_detail)
                                    if '$ref' not in item_detail else
                                    self.construct(util.resolve_ref_uri(
                                        self.resolver.resolution_scope,
                                        item_detail['$ref']),
                                        item_detail)

                                    for i, item_detail in enumerate(detail['items']['oneOf'])]
                                    )
                            else:
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
          elif addlProp is True:
            props['__extensible__'] = True
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
                required.add(prop)

        invalid_requires = [req for req in required if req not in props['__propinfo__']]
        if len(invalid_requires) > 0:
          raise validators.ValidationError("Schema Definition Error: {0} schema requires "
                                           "'{1}', but properties are not defined"
                                           .format(nm, invalid_requires))

        props['__required__'] = required

        cls = type(str(nm.split('/')[-1]), tuple(parents), props)

        return cls


def make_property(prop, info, desc=""):

    def getprop(self):
        try:
            return self._properties[prop]
        except KeyError:
            raise AttributeError("No such attribute")

    def setprop(self, val):
        if isinstance(info['type'], (list, tuple)):
            ok = False
            errors = []
            type_checks = []

            for typ in info['type']:
              if not isinstance(typ, dict):
                type_checks.append(typ)
                continue
              typ = ProtocolBase.__SCHEMA_TYPES__[typ['type']]
              if typ is None:
                  typ = type(None)
              if isinstance(typ, (list, tuple)):
                  type_checks.extend(typ)
              else:
                  type_checks.append(typ)

            for typ in type_checks:
                if isinstance(val, typ):
                    ok = True
                    break
                elif hasattr(typ, 'isLiteralClass'):
                    try:
                        validator = typ(val)
                    except Exception as e:
                        errors.append(
                            "Failed to coerce to '{0}': {1}".format(typ, e))
                        pass
                    else:
                        validator.validate()
                        ok = True
                        break
                elif util.safe_issubclass(typ, ProtocolBase):
                    # force conversion- thus the val rather than validator assignment
                    try:
                        val = typ(**util.coerce_for_expansion(val))
                    except Exception as e:
                        errors.append(
                            "Failed to coerce to '{0}': {1}".format(typ, e))
                        pass
                    else:
                        val.validate()
                        ok = True
                        break
                elif util.safe_issubclass(typ, validators.ArrayValidator):
                    try:
                        val = typ(val)
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
                raise validators.ValidationError(
                    "Object must be one of {0}: \n{1}".format(info['type'], errstr))

        elif info['type'] == 'array':
            instance = info['validator'](val)
            val = instance.validate()

        elif getattr(info['type'], 'isLiteralClass', False) is True:
            if not isinstance(val, info['type']):
                validator = info['type'](val)
            validator.validate()

        elif util.safe_issubclass(info['type'], ProtocolBase):
            if not isinstance(val, info['type']):
                val = info['type'](**util.coerce_for_expansion(val))

            val.validate()
        elif info['type'] is None:
            # This is the null value
            if val is not None:
                raise validators.ValidationError(
                    "None is only valid value for null")
        
        else:
            raise TypeError("Unknown object type: '{0}'".format(info['type']))

        self._properties[prop] = val

    def delprop(self):
        if prop in self.__required__:
            raise AttributeError("'%s' is required" % prop)
        else:
            del self._properties[prop]

    return property(getprop, setprop, delprop, desc)
