# -*- coding: spec -*-
import nose
import nose.tools
from sure import expect, this
import pkg_resources

import json
from noseOfYeti.tokeniser.support import noy_sup_setUp
from unittest import TestCase
import nose

import python_jsonschema_objects as pjs
from python_jsonschema_objects.validators import ValidationError, ArrayValidator

md = pkg_resources.resource_filename('python_jsonschema_objects',
        '../README.md')
examples = pjs.markdown_support.extract_code_blocks(md)
example = json.loads(examples['schema'][0])
builder = pjs.ObjectBuilder(example)
Person = builder.build_classes().ExampleSchema


describe TestCase, 'ArrayValidator':

  before_each:
    pass

  context '#create':

    it 'should support empty validations':
        ArrayValidator.create.when.called_with('hello').should_not.throw()

    context 'item validations':

        it 'should support dictionaries as item validators':
            ArrayValidator.create.when.called_with(
                'hello',
                item_constraint={'type': 'string'}
                ).should_not.throw()

        it 'should support tuples as item validators':
            ArrayValidator.create.when.called_with(
                'hello',
                item_constraint=[{'type': 'string'}, {'type': 'string'}]
                ).should_not.throw()

        it 'should throw an error if item validators are not classes or dicts':
            ArrayValidator.create.when.called_with(
                'hello',
                item_constraint=['winner']
                ).should.throw(TypeError)

  context 'validate':

    it 'should validate basic array types':
      validator = ArrayValidator.create(
          'test',
          item_constraint={'type': 'number'}
      )

      instance = validator([1,2,3,4])

      instance.validate.when.called_with().should_not.throw(ValidationError)

      instance = validator([1, 2, "Hello"])
      instance.validate.when.called_with().should.throw(ValidationError)

    it 'should validate basic tuple types':
      validator = ArrayValidator.create(
          'test',
          item_constraint=[{'type': 'number'}, {'type': 'number'}]
      )

      instance = validator([1,2,3,4])

      instance.validate.when.called_with().should_not.throw(ValidationError)

      instance = validator([1, "Hello"])
      instance.validate.when.called_with().should.throw(ValidationError)


    it 'should validate arrays with object types':
      validator = ArrayValidator.create(
          'test',
          item_constraint=Person
      )

      instance = validator([{'firstName': 'winner', 'lastName': 'Dinosaur'} ])
      instance.validate.when.called_with().should_not.throw(ValidationError)

      instance = validator([{'firstName': 'winner', 'lastName': 'Dinosaur'}, {'firstName': 'BadMan'} ])
      instance.validate.when.called_with().should.throw(ValidationError)

    it 'should validate tuples with mixed types':

      validator = ArrayValidator.create(
          'test',
          item_constraint=[Person, {'type': 'number'}]
      )

      instance = validator([{'firstName': 'winner', 'lastName': 'Dinosaur'}, 'fried' ])
      instance.validate.when.called_with().should.throw(ValidationError)

      instance = validator([{'firstName': 'winner', 'lastName': 'Dinosaur'}, 12324 ])
      instance.validate.when.called_with().should_not.throw(ValidationError)

    it 'should validate nested arrays':

      validator = ArrayValidator.create(
          'test',
          item_constraint={'type': 'array', 'items': {'type': 'integer'}}
      )

      instance = validator([[1,2,4,5], [1,2,4]])
      instance.validate.when.called_with().should_not.throw(ValidationError)

      instance = validator([[1,2,'h',5], [1,2,4]])
      instance.validate.when.called_with().should.throw(ValidationError)

      instance = validator([[1,2,'h',5], [1,2,'4']])
      instance.validate.when.called_with().should.throw(ValidationError)

    it 'should validate length':
      validator = ArrayValidator.create(
          'test',
          minItems=1,
          maxItems=3
      )

      instance = validator(range(1))
      instance.validate.when.called_with().should_not.throw(ValidationError)

      instance = validator(range(2))
      instance.validate.when.called_with().should_not.throw(ValidationError)

      instance = validator(range(3))
      instance.validate.when.called_with().should_not.throw(ValidationError)

      instance = validator(range(4))
      instance.validate.when.called_with().should.throw(ValidationError)

      instance = validator([])
      instance.validate.when.called_with().should.throw(ValidationError)

    it 'should validate uniqueness':
      validator = ArrayValidator.create(
          'test',
          uniqueItems=True
      )

      instance = validator([])
      instance.validate.when.called_with().should_not.throw(ValidationError)

      instance = validator([1,2,3,4])
      instance.validate.when.called_with().should_not.throw(ValidationError)

      instance = validator([1,2,2,4])
      instance.validate.when.called_with().should.throw(ValidationError, 'uniqueness')
