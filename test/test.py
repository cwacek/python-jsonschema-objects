# -*- coding: spec -*-
# This is a comparison of DSL syntax to what is generated

import nose
import nose.tools
from sure import expect, this

import json
from noseOfYeti.tokeniser.support import noy_sup_setUp
from unittest import TestCase
import nose

import pkg_resources
import python_jsonschema_objects as pjs

describe TestCase, 'markdown extraction':

    before_each:
        md = pkg_resources.resource_filename('python_jsonschema_objects',
                '../README.md')
        self.examples = pjs.markdown_support.extract_code_blocks(md)
        self.examples = {json.loads(v)['title']: json.loads(v) for v in self.examples['schema']}
        self.example = self.examples['Example Schema']

    it 'loads schema files':
        self.examples.should.have.key('Other')

    describe 'ObjectBuilder':

        it 'should load memory: references':

            builder = pjs.ObjectBuilder(self.examples['Other'], resolved=self.examples)
            builder.should.be.ok

            builder.validate.when.called_with({'MyAddress': 1234}).should.throw(pjs.ValidationError)
            builder.validate.when.called_with({'MyAddress': '1234'}).should_not.throw(pjs.ValidationError)

        it 'should be able to read an object':
            for nm, ex in self.examples.iteritems():
                builder = pjs.ObjectBuilder(ex, resolved=self.examples)
                builder.should.be.ok

        context "additionalProperties":

            before_each:
                builder = pjs.ObjectBuilder(self.examples['Example Schema'], resolved=self.examples)
                builder.should.be.ok
                self.Person = builder.classes['ExampleSchema']
                builder = pjs.ObjectBuilder(self.examples['Other'], resolved=self.examples)
                builder.should.be.ok
                self.Other = builder.classes['Other']

            it 'should allow additionalProperties by default':

                def set_attribute(object):
                    object.randomAttribute = 4

                person = self.Person()
                set_attribute.when.called_with(person).should_not.throw(Exception)

                int(person.randomAttribute).should.equal(4)

            it 'should still raise errors when accessing undefined attributes':

                person = self.Person()
                #person.should_not.have.property('randomAttribute')

            it 'should not allow undefined attributes if false':

                def set_attribute(object):
                    object.randomAttribute = 4

                other = self.Other()
                set_attribute.when.called_with(other).should.throw(pjs.ValidationError)

        context 'PersonExample':
            before_each:
                self.builder = pjs.ObjectBuilder(self.example, resolved=self.examples )
                namespace = self.builder.build_classes()
                self.Person = namespace.ExampleSchema

            it 'should allow empty objects':
                person = self.Person()
                person.should.be.ok

            it 'should allow attributes to be given':
                person = self.Person(firstName="James",
                        lastName="Bond", age=35)
                str(person.firstName).should.equal("James")
                str(person.lastName).should.equal("Bond")
                int(person.age).should.equal(35)
                person.should.be.ok

            it 'should validate when decoding from json':
                self.Person.from_json.when.called_with(
                        '{"firstName":"James"}'
                        ).should.throw(pjs.ValidationError)

            it 'should validate enumerations':
                person = self.Person()

                def set_gender(gender):
                    person.gender = gender

                set_gender.when.called_with("robot").should.throw(pjs.ValidationError)
                set_gender.when.called_with("male").should_not.throw(pjs.ValidationError)
                set_gender.when.called_with("female").should_not.throw(pjs.ValidationError)

            it 'should validate mixed-type enumerations':
                person = self.Person()

                def set_status(status):
                    person.deceased = status

                set_status.when.called_with("robot").should.throw(pjs.ValidationError)
                set_status.when.called_with("yes").should_not.throw(pjs.ValidationError)
                set_status.when.called_with("no").should_not.throw(pjs.ValidationError)
                set_status.when.called_with(1).should_not.throw(pjs.ValidationError)
                set_status.when.called_with(2).should.throw(pjs.ValidationError)
                set_status.when.called_with(2.3).should.throw(pjs.ValidationError)


            it 'should allow non-required attributes to be missing':
                person = self.Person(firstName="James",
                        lastName="Bond")
                person.should.be.ok
                str(person.firstName).should.equal("James")
                str(person.lastName).should.equal("Bond")

            it 'should not allow required attributes to be missing':
                person = self.Person(firstName="James")

                person.validate.when.called_with().should.throw(
                        pjs.ValidationError
                        )

            it 'should validate minimum age':
                self.Person.when.called_with(
                        firstName="James", lastName="Bond",
                        age=-10).should.throw(pjs.ValidationError)

                person = self.Person(firstName="James",
                        lastName="Bond")

                def setage(x):
                    person.age = x

                setage.when.called_with(-1).should.throw(pjs.ValidationError)

            it 'should validate before serializing':
                person = self.Person(firstName="James",
                        lastName="Bond")

                person._properties['age'] = -1

                person.serialize.when.called_with().should.throw(pjs.ValidationError)

            it 'should remove null values when serializing':
                person = self.Person(firstName="James",
                        lastName="Bond")

                json_str = person.serialize()
                json.loads(json_str).should_not.have.key('age')

            it 'should serialize lists':
                person = self.Person(
                        firstName="James",
                        lastName="Bond",
                        dogs=["Lassie", "Bobo"]
                        )

                json_str = person.serialize()
                json.loads(json_str).should.equal(
                    {
                      'firstName': "James",
                      'lastName': "Bond",
                      'dogs': ["Lassie", "Bobo"]
                      }
                    )

            it 'should transform into dictionaries recursively"':
                pdict = dict(
                        firstName="James",
                        lastName="Bond",
                        dogs=["Lassie", "Bobo"]
                        )

                person = self.Person( **pdict)

                person.as_dict().should.equal(pdict)
