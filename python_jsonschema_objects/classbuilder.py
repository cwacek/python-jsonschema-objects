import python_jsonschema_objects.util as util
import python_jsonschema_objects.validators as validators
import python_jsonschema_objects.pattern_properties as pattern_properties
from python_jsonschema_objects.literals import LiteralValue

import collections
import itertools
import six
import sys

import logging

import python_jsonschema_objects.wrapper_types

logger = logging.getLogger(__name__)

logger.addHandler(logging.NullHandler())


# Long is no longer a thing in python3.x
if sys.version_info > (3,):
  long = int


class UnresolvedProperty(
        collections.namedtuple('UnresolvedProperty',
                               'uri, property_name, refuri')):
    """ Represents the information needed to attach a property
    to a class.

    Args:
        uri: (str) The URI of the class with the property
        property_name: (str) the name of the unresolved property
        refuri: (str) the URI of the object that should represent
            this property
    """

    def apply(self, klass, resolve_map={}):
        """ Attach this property to the provided class

        Args:
            klass: (ProtocolBase) The class wrapper to which this
                property should be attached.
            resolve_map: (dict) A map of URIs to resolved ProtocolBase
                objects.
        """
        assert util.safe_issubclass(klass, ProtocolBase)

        resolved_property = make_property(self.property_name,
                                          {'type': resolve_map[self.refuri]},
                                          resolve_map[self.refuri].__doc__)

        setattr(klass, self.property_name, resolved_property)
        klass.__propinfo__[self.property_name] = {
            "$ref": self.refuri,
            "type": resolve_map[self.refuri]
        }


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
    __has_default__ = set()
    __object_attr_list__ = set(["_properties", "_extended_properties"])

    def as_dict(self):
        """ Return a dictionary containing the current values
        of the object.

        Returns:
            (dict): The object represented as a dictionary
        """
        out = {}
        for prop in self:
            propval = getattr(self, prop)

            if hasattr(propval, 'for_json'):
                out[prop] = propval.for_json()
            elif isinstance(propval, list):
                out[prop] = [getattr(x, 'for_json', lambda:x)() for x in propval]
            elif isinstance(propval, (ProtocolBase, LiteralValue)):
                out[prop] = propval.as_dict()
            elif propval is not None:
                out[prop] = propval

        return out

    def for_json(self):
        return self.as_dict()

    def __eq__(self, other):
        if not isinstance(other, ProtocolBase):
            return False

        return self.as_dict() == other.as_dict()

    def __str__(self):
        inverter = dict((v, k) for k,v in six.iteritems(self.__prop_names__))
        props = sorted(["%s" % (inverter.get(k, k),) for k, v in
                 itertools.chain(six.iteritems(self._properties),
                                 six.iteritems(self._extended_properties))])
        return "<%s attributes: %s>" % (self.__class__.__name__, ", ".join(props))

    def __repr__(self):
        inverter = dict((v, k) for k,v in six.iteritems(self.__prop_names__))
        props = sorted(["%s=%s" % (inverter.get(k, k), repr(v)) for k, v in
                 itertools.chain(six.iteritems(self._properties),
                                 six.iteritems(self._extended_properties))])
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
                "".join("{0}: {1}\n".format(k, e) for k, e in validation_errors)
            )

        return obj

    def __init__(self, **props):
        self._extended_properties = dict()
        self._properties = dict(zip(self.__prop_names__.values(),
                                    [None for x in
                                     six.moves.xrange(len(self.__prop_names__))]))

        # To support defaults, we have to actually execute the constructors
        # but only for the ones that have defaults set.
        for name in self.__has_default__:
            if name not in props:
                logger.debug(util.lazy_format("Initializing '{0}' ", name))
                setattr(self, name, None)

        for prop in props:
            try:
                logger.debug(util.lazy_format(
                    "Setting value for '{0}' to {1}", prop, props[prop]))
                if props[prop] is not None:
                    setattr(self, prop, props[prop])
            except validators.ValidationError as e:
                import sys
                raise six.reraise(
                    type(e),
                    type(e)(str(e) + " \nwhile setting '{0}' in {1}".format(
                        prop, self.__class__.__name__)), sys.exc_info()[2])

        if getattr(self, '__strict__', None):
            self.validate()

    def __setattr__(self, name, val):
        if name in self.__object_attr_list__:
            object.__setattr__(self, name, val)
        elif name in self.__propinfo__:
            # If its in __propinfo__, then it actually has a property defined.
            # The property does special validation, so we actually need to
            # run its setter. We get it from the class definition and call
            # it directly. XXX Heinous.
            prop = getattr(self.__class__, self.__prop_names__[name])
            prop.fset(self, val)
        else:
            # This is an additional property of some kind
            try:
                val = self.__extensible__.instantiate(name, val)
            except Exception as e:
                raise validators.ValidationError(
                    "Attempted to set unknown property '{0}': {1} "
                    .format(name, e))

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

    def serialize(self, **opts):
        self.validate()
        enc = util.ProtocolJSONEncoder(**opts)
        return enc.encode(self)

    def validate(self):
        """ Applies all defined validation to the current
        state of the object, and raises an error if
        they are not all met.

        Raises:
            ValidationError: if validations do not pass
        """

        missing = self.missing_property_names()

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

    def missing_property_names(self):
        """
        Returns a list of properties which are required and missing.

        Properties are excluded from this list if they are allowed to be null.

        :return: list of missing properties.
        """

        propname = lambda x: self.__prop_names__[x]
        missing = []
        for x in self.__required__:

            # Allow the null type
            propinfo = self.propinfo(propname(x))
            null_type = False
            if 'type' in propinfo:
                null_type = propinfo['type'] == 'null'
            elif 'oneOf' in propinfo:
                for o in propinfo['oneOf']:
                    if 'type' in o and o['type'] == 'null':
                        null_type = True
                        break

            if (propname(x) not in self._properties and null_type) or \
                    (self._properties[propname(x)] is None and not null_type):
                missing.append(x)

        return missing


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
                obj.validate()
            except TypeError as e:
                validation_errors.append((klass, e))
            except validators.ValidationError as e:
                validation_errors.append((klass, e))
            else:
                return obj

        else:  # We got nothing
            raise validators.ValidationError(
                "Unable to instantiate any valid types: \n"
                "".join("{0}: {1}\n".format(k, e) for k, e in validation_errors)
            )




class ClassBuilder(object):

    def __init__(self, resolver):
        self.resolver = resolver
        self.resolved = {}
        self.under_construction = list()
        """ Tracks a list of properties that need to
        be resolved because they weren't able to be
        resolved at the time."""
        self.pending = set()

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
        if ('override' not in kw or kw['override'] is False) \
                and uri in self.resolved:
            logger.debug(util.lazy_format("Using existing {0}", uri))
            return self.resolved[uri]
        else:
            ret = self._construct(uri, *args, **kw)
        logger.debug(util.lazy_format("Constructed {0}", ret))

        # processing pending items
        for pending_item in self.pending:
            logger.debug(util.lazy_format(
                "Atttempting to resolve property "
                "{0.property_name} for {0.uri}",
                pending_item))

            if pending_item.refuri not in self.resolved:
                continue

            if pending_item.uri not in self.resolved:
                raise ValueError(
                    "{0} refers to {1}, but {0} has not been resolved"
                    .format(pending_item.uri, pending_item.refuri))

            target_class = self.resolved[pending_item.uri]
            pending_item.apply(target_class, self.resolved)

        return ret

    def _construct(self, uri, clsdata, parent=(ProtocolBase,),**kw):

        if 'anyOf' in clsdata:
            raise NotImplementedError(
                "anyOf is not supported as bare property")

        elif 'oneOf' in clsdata:
            self.resolved[uri] = self._build_object(
                uri,
                clsdata,
                parent, **kw)
            return self.resolved[uri]

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
                parents,**kw)
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
                ref = clsdata['$ref']
                refuri = util.resolve_ref_uri(
                    self.resolver.resolution_scope, ref)
                logger.debug(
                    util.lazy_format(
                        "Resolving direct reference object for {0}: {1}",
                        uri,
                        refuri))

                with self.resolver.resolving(refuri) as resolved:
                    self.resolved[uri] = self.construct(
                        refuri,
                        resolved,
                        parent)

            return self.resolved[uri]

        elif clsdata.get('type') == 'array' and 'items' in clsdata:
            clsdata_copy = {}
            clsdata_copy.update(clsdata)
            self.resolved[uri] = python_jsonschema_objects.wrapper_types.ArrayWrapper.create(
                uri,
                item_constraint=clsdata_copy.pop('items'),
                classbuilder=self,
                **clsdata_copy)
            return self.resolved[uri]

        elif isinstance(clsdata.get('type'), list):
            types = []
            for i, item_detail in enumerate(clsdata['type']):
                subdata = {k: v for k, v in six.iteritems(clsdata) if k != 'type'}
                subdata['type'] = item_detail
                types.append(self._build_literal(
                    uri + "_%s" % i,
                    subdata))

            self.resolved[uri] = TypeProxy(types)
            return self.resolved[uri]

        elif (clsdata.get('type', None) == 'object' or
              clsdata.get('properties', None) is not None or
              clsdata.get('additionalProperties', False)):
            self.resolved[uri] = self._build_object(
                uri,
                clsdata,
                parent,**kw)
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
        '__propinfo__': {
            '__literal__': clsdata,
            '__default__': clsdata.get('default')}
        })

      return cls

    def _build_object(self, nm, clsdata, parents,**kw):
        logger.debug(util.lazy_format("Building object {0}", nm))

        # To support circular references, we tag objects that we're
        # currently building as "under construction"
        self.under_construction.append(nm)

        props = {}
        defaults = set()

        properties = {}
        for p in parents:
            properties = util.propmerge(properties, p.__propinfo__)

        if 'properties' in clsdata:
            properties = util.propmerge(properties, clsdata['properties'])

        name_translation = {}

        for prop, detail in properties.items():
            logger.debug(util.lazy_format("Handling property {0}.{1}",nm, prop))
            properties[prop]['raw_name'] = prop
            name_translation[prop] = prop.replace('@', '')
            prop = name_translation[prop]

            if detail.get('default', None) is not None:
                defaults.add(prop)

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
                logger.debug(util.lazy_format(
                    "Resolving reference {0} for {1}.{2}",
                    ref, nm, prop
                ))
                if uri not in self.resolved:
                    """
                    if $ref is under construction, then we're staring at a
                    circular reference.  We save the information required to
                    construct the property for later.
                    """
                    if uri in self.under_construction:
                        self.pending.add(
                            UnresolvedProperty(
                                uri=nm,
                                property_name=prop,
                                refuri=uri
                            )
                        )
                        continue

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
                            'validator': python_jsonschema_objects.wrapper_types.ArrayWrapper.create(
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
                                        'validator': python_jsonschema_objects.wrapper_types.ArrayWrapper.create(uri, item_constraint=typ,
                                                                                                                 addl_constraints=detail)}
                        except NotImplementedError:
                            typ = detail['items']
                            propdata = {'type': 'array',
                                        'validator': python_jsonschema_objects.wrapper_types.ArrayWrapper.create(uri,
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

        props['__extensible__'] = pattern_properties.ExtensibleValidator(
            nm,
            clsdata,
            self)

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
        props['__has_default__'] = defaults
        if required and kw.get("strict"):
            props['__strict__'] = True
        cls = type(str(nm.split('/')[-1]), tuple(parents), props)
        self.under_construction.remove(nm)

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
              typ = next(t
                         for n, t in validators.SCHEMA_TYPE_MAPPING
                         if typ['type'] == n)
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
                elif util.safe_issubclass(typ, python_jsonschema_objects.wrapper_types.ArrayWrapper):
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
            val = info['validator'](val)
            val.validate()

        elif util.safe_issubclass(info['type'],
                                  python_jsonschema_objects.wrapper_types.ArrayWrapper):
            # An array type may have already been converted into an ArrayValidator
            val = info['type'](val)
            val.validate()

        elif getattr(info['type'], 'isLiteralClass', False) is True:
            if not isinstance(val, info['type']):
                validator = info['type'](val)
                validator.validate()
                if validator._value is not None:
                    # This allows setting of default Literal values
                    val = validator

        elif util.safe_issubclass(info['type'], ProtocolBase):
            if not isinstance(val, info['type']):
                val = info['type'](**util.coerce_for_expansion(val))

            val.validate()

        elif isinstance(info['type'], TypeProxy):
            val = info['type'](val)

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
