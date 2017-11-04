def MakeLiteral(name, typ, value, **properties):
    properties.update({'type': typ})
    klass = type(str(name), tuple((LiteralValue,)), {
        '__propinfo__': {
            '__literal__': properties,
            '__default__': properties.get('default')
        }
    })

    return klass(value)

class LiteralValue(object):
  """Docstring for LiteralValue """

  isLiteralClass = True

  def __init__(self, value, typ=None):
      """@todo: to be defined

      :value: @todo

      """
      if isinstance(value, LiteralValue):
          self._value = value._value
      else:
          self._value = value

      if self._value is None and self.default() is not None:
          self._value = self.default()

      self.validate()

  def as_dict(self):
      return self.for_json()

  def for_json(self):
      return self._value

  @classmethod
  def default(cls):
      return cls.__propinfo__.get('__default__')

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

  def __str__(self):
      return str(self._value)

  def validate(self):
      info = self.propinfo('__literal__')

      # this duplicates logic in validators.ArrayValidator.check_items; unify it.
      for param, paramval in sorted(six.iteritems(info), key=lambda x: x[0].lower() != 'type'):
          validator = validators.registry(param)
          if validator is not None:
              validator(paramval, self._value, info)

  def __eq__(self, other):
      return self._value == other

  def __hash__(self):
      return hash(self._value)

  def __lt__(self, other):
      return self._value < other

  def __int__(self):
    return int(self._value)

  def __float__(self):
    return float(self._value)
