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

Resource
  get_uri() → uri
  get_sync_status() → str
      return "ok" if the resource is in sync with the data at its URI,
      else any other string describing the reason why it is not.
  get_readonly() → bool
      return true if this resource is not modifiable
  remove()
      remove this resource from the KTBS
      If the resource can not be removed, an exception must be raised.
  get_label() → str
      returns a user-friendly label
  set_label(str)
      set a user-friendly label
  reset_label()
      reset the user-friendly label to its default value

Base (Base)
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

class TestKtbsClientBaseResource(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_get_base_uri(self):
        reference_uri = URIRef(KTBS_ROOT + "BaseTest/")
        assert self.base.get_uri() == reference_uri

    @skip("Resource.get_sync_status() is not yet implemented")
    def test_get_sync_status(test):
        assert self.base.get_sync_status() == "ok"

    def test_get_readonly(self):
        assert self.base.get_readonly() == False

    def test_get_base_label(self):
        assert self.base.get_label() == "Test base"

    @skip("Resource.set_label() does not work for base : 403 forbidden")
    def test_set_base_label(self):
        self.base.set_label("New base label")
        assert self.base.get_label() == "New base label"

    @skip("Resource.reset_label() is not yet implemented")
    def test_reset_base_label(self):
        self.base.reset_label()
        assert self.base.get_label() == "Test base"

    @skip("Resource.remove() does not work : 405 Not Allowed")
    def test_remove_base(self):
        base_uri = self.base.get_uri()
        self.base.remove()
        assert self.root.get_base(base_uri) == None

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
        mod = self.base.create_model()
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/model")
        assert mod.get_uri() == generated_uri

    def test_create_model_with_id(self):
        mod = self.base.create_model(id="ModelWithID")
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/ModelWithID")
        assert mod.get_uri() == generated_uri

    def test_create_model_with_label(self):
        mod = self.base.create_model(label="Model with label")
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/model-with-label")
        assert mod.get_uri() == generated_uri

    def test_list_models(self):
        lmod = self.base.list_models()
        assert len(lmod) == 3

    def test_get_model(self):
        model_uri = URIRef(KTBS_ROOT + "BaseTest/ModelWithID")
        mod = self.base.get(model_uri)
        assert mod.get_uri() == model_uri

    def test_create_stored_trace_no_id_no_label(self):
        model_uri = URIRef(KTBS_ROOT + "BaseTest/ModelWithID")
        st = self.base.create_stored_trace(model_uri)
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/storedtrace/")
        assert st.get_uri() == generated_uri

    def test_create_stored_trace_with_id(self):
        model_uri = URIRef(KTBS_ROOT + "BaseTest/ModelWithID")
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/StoredTraceWithID/")
        st = self.base.create_stored_trace(model_uri, id="StoredTraceWithID/")
        assert st.get_uri() == generated_uri

    def test_create_stored_trace_with_label(self):
        model_uri = URIRef(KTBS_ROOT + "BaseTest/ModelWithID")
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/stored-trace-with-label/")
        st = self.base.create_stored_trace(model_uri, label="stored-trace-with-label")
        assert st.get_uri() == generated_uri

    def test_list_stored_traces(self):
        lt = self.base.list_traces()
        assert len(lt) == 3

    def test_get_stored_trace(self):
        trace_uri = URIRef(KTBS_ROOT + "BaseTest/StoredTraceWithID/")
        st = self.base.get(trace_uri)
        assert st.get_uri() == trace_uri

    @skip("Base.create_method is not implemented yet")
    def test_create_method_no_id_no_label(self):
        # A method should always be build upon a parent one
        # So first on builtin methods ?
        #for m in self.root.list_builtin_methods():
        method_uri = "fake"
        generated_uri = "fake"
        meth = self.base.create_method(method_uri)
        assert meth.get_uri() == generated_uri

    @skip("Base.list_methods is not usable yet - no method created")
    def list_methods():
        lt = self.base.list_methods()
        assert len(lt) == 1

    @skip("Base.get(method_uri) is not usable yet - no method created")
    def test_get_method(self):
        method_uri = "fake"
        meth = self.base.get(method_uri)
        assert meth.get_uri() == method_uri

    @skip("Base.create_computed_trace is not implemented yet")
    def test_create_computed_trace_no_id_no_label(self):
        # A computed trace could have no source ???
        #for m in self.root.list_builtin_methods():
        method_uri = "fake"
        source_trace_uri = URIRef(KTBS_ROOT + "BaseTest/StoredTraceWithID/")
        generated_uri = "fake"
        ct = self.base.create_computed_trace(method_uri)
        assert ct.get_uri() == generated_uri

    @skip("Base.list_traces() will not render computed trace yet")
    def test_list_stored_traces(self):
        lt = self.base.list_traces()
        assert len(lt) == 4

    @skip("Base.get(computed_trace_uri) is not usable yet")
    def test_get_computed_trace(self):
        trace_uri = URIRef(KTBS_ROOT + "BaseTest/ComputedTraceWithID/")
        st = self.base.get(trace_uri)
        assert st.get_uri() == trace_uri

