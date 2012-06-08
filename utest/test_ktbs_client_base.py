#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/silex/2009/ktbs>
#    Copyright (C) 2012 Françoise Conil <fconil@liris.cnrs.fr> / SILEX
#
#    KTBS is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    KTBS is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with KTBS.  If not, see <http://www.gnu.org/licenses/>.

"""
Nose unit-testing for the kTBS base client API.


  get(id:uri) → Trace|Model|Method|ObselType|AttributeType|RelationType|Obsel
      return the element of this base identified by the given URI, or null
  list_traces() → [Trace]
  list_models() → [Model]
      list the models stored in that base
  list_methods() → [Method]
      list the methods stored in that base
  create_stored_trace(model:Model, origin:str?, default_subject:str?,
                      label:str?, id:uri?)
                     → StoredTrace
      list the stored traces stored in that base
      if origin is not specified, a fresh opaque string is generated
  create_computed_trace(method:Method, sources:[Trace]?, label:str?, id:uri?)
                       → ComputedTrace
      list the computed traces stored in that base
  create_model(parents:[Model]?, label:str?, id:uri?) → Model
  create_method(parent:Method, parameters:[str=>any]?, label:str?,
                id:uri) → Method
"""
from unittest import TestCase, skip

from os.path import abspath, dirname, join
from subprocess import Popen, PIPE

from rdflib import URIRef

from ktbs.namespaces import KTBS

from ktbs.client.root import KtbsRoot

KTBS_ROOT = "http://localhost:8001/"

class TestKtbsClientBase(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_create_model_no_id_no_label(self):
        m = self.base.create_model()
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/model")
        assert m.get_uri() == generated_uri

    def test_create_model_with_id(self):
        m = self.base.create_model(id="ModelWithID")
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/ModelWithID")
        assert m.get_uri() == generated_uri

    def test_create_model_with_label(self):
        m = self.base.create_model(label="Model with label")
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/model-with-label")
        assert m.get_uri() == generated_uri

    def test_list_models(self):
        lm = self.base.list_models()
        assert len(lm) == 3

