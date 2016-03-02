# -*- coding: spec -*-
# This is a comparison of DSL syntax to what is generated

import six
import nose
import nose.tools
from sure import expect, this

import json
from noseOfYeti.tokeniser.support import noy_sup_setUp
from unittest import TestCase
import os.path

import pkg_resources
import python_jsonschema_objects as pjs


describe TestCase 'RegressionFiles':

    describe 'swagger.json':

        before_each:
            self.fname = os.path.join(
                    os.path.dirname(__file__),
                    'resources',
                    'swagger.json'
                    )

        it 'should not recurse infinitely':

            builder = pjs.ObjectBuilder(self.fname)

            namespace = builder.build_classes()
