#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
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
"""
from unittest import TestCase, skip
from nose.tools import assert_raises, eq_

from rdflib import URIRef
from rdfrest.exceptions import InvalidDataError, RdfRestException

from ktbs.namespace import KTBS

from .test_ktbs_engine import KtbsTestCase

KTBS_ROOT = "http://localhost:12345/"

class TestKtbsBase(KtbsTestCase):

    def setUp(self):
        KtbsTestCase.setUp(self)
        self.base = self.my_ktbs.create_base(id="BaseTest/", label="Test base")

    ######## get information ########

    def test_get_base_uri(self):
        reference_uri = URIRef(KTBS_ROOT + "BaseTest/")
        eq_(self.base.get_uri(), reference_uri)

    @skip("Resource.get_sync_status() is not yet implemented")
    def test_get_sync_status(test):
        eq_(self.base.get_sync_status(), "ok")

    def test_get_readonly(self):
        eq_(self.base.get_readonly(), False)

    def test_get_base_label(self):
        eq_(self.base.get_label(), "Test base")

    ######## set information ########

    def test_set_base_label(self):
        self.base.set_label("New base label")
        eq_(self.base.get_label(), "New base label")

    def test_reset_base_label(self):
        self.base.reset_label()
        eq_(self.base.get_label(), "BaseTest")

    ######## add model ########

    def test_create_model_no_id_no_label(self):
        mod = self.base.create_model()
        # it should just work, but we don't really care about the URI

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id=mod.uri)

    def test_create_model_with_id(self):
        mod = self.base.create_model(id="ModelWithID")
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/ModelWithID")
        eq_(mod.get_uri(), generated_uri)

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="ModelWithID")

    def test_create_model_with_folderish_id(self):
        mod = self.base.create_model(id="ModelWithID/")
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/ModelWithID/")
        eq_(mod.get_uri(), generated_uri)

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="ModelWithID/")

    def test_create_model_with_label(self):
        mod = self.base.create_model(label="Model with label")
        # it should just work, but we don't really care about the URI

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id=mod.uri)

    def test_create_two_models(self):
        # check that independantly created models have different URIs,
        # even if they have the same label
        mod1 = self.base.create_model(label="Duplicate label")
        mod2 = self.base.create_model(label="Duplicate label")
        eq_(mod1.label, mod2.label)
        assert mod1.uri != mod2.uri

    def test_create_bad_model_id(self):
        # ID not inside this base
        other_base = self.my_ktbs.create_base()
        wrong_uri = URIRef("WrongID", other_base.uri)
        with assert_raises(InvalidDataError):
            self.base.create_model(id=wrong_uri)
        # wrong ID
        with assert_raises(InvalidDataError):
            self.base.create_model(id="@WrongID")
        with assert_raises(InvalidDataError):
            self.base.create_model(id="Wrong/ID")

    ######## add stored trace ########

    def test_create_stored_trace_no_id_no_label(self):
        st = self.base.create_stored_trace(model="http://example.org/model")
        # it should just work, but we don't really care about the URI

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_stored_trace(id=st.uri,
                                          model="http://example.org/model")

    def test_create_stored_trace_with_id(self):
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/StoredTraceWithID/")
        st = self.base.create_stored_trace(id="StoredTraceWithID/",
                                           model="http://example.org/model")
        eq_(st.get_uri(), generated_uri)

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_stored_trace(id="StoredTraceWithID/",
                                           model="http://example.org/model")

    def test_create_stored_trace_with_label(self):
        st = self.base.create_stored_trace(model="http://example.org/model", 
                                           label="stored-trace-with-label")
        # it should just work, but we don't really care about the URI

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_stored_trace(id=st.uri,
                                          model="http://example.org/model")

    def test_create_two_stored_traces(self):
        # check that independantly created stored traces have different URIs,
        # even if they have the same label
        trc1 = self.base.create_stored_trace(model="http://example.org/model",
                                             label="Duplicate label")
        trc2 = self.base.create_stored_trace(model="http://example.org/model",
                                             label="Duplicate label")
        eq_(trc1.label, trc2.label)
        assert trc1.uri != trc2.uri

    def test_create_bad_stored_trace(self):
        # ID not inside this base
        other_base = self.my_ktbs.create_base()
        wrong_uri = URIRef("WrongID", other_base.uri)
        with assert_raises(InvalidDataError):
            self.base.create_stored_trace(id=wrong_uri,
                                          model="http://example.org/model")
        # wrong id
        with assert_raises(InvalidDataError):
            self.base.create_stored_trace(id="WrongID", # no slash
                                          model="http://example.org/model")
        with assert_raises(InvalidDataError):
            self.base.create_stored_trace(id="@WrongID/", # invalid character @
                                          model="http://example.org/model")
        with assert_raises(InvalidDataError):
            self.base.create_stored_trace(id="Wrong/ID/", # invalid character /
                                          model="http://example.org/model")
        # no model
        with assert_raises(ValueError):
            self.base.create_stored_trace(id="StoredTraceWithID/")
                
    ######## add method ########

    def test_create_method_no_id_no_label(self):
        meth = self.base.create_method(parent=KTBS.filter)
        # it should just work, but we don't really care about the URI

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_method(id=meth.uri, parent=KTBS.filter)

    def test_create_method_with_id(self):
        meth = self.base.create_method(id="MethodWithID", parent=KTBS.filter)
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/MethodWithID")
        eq_(meth.get_uri(), generated_uri)

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_method(id="MethodWithID", parent=KTBS.filter)

    def test_create_method_with_label(self):
        meth = self.base.create_method(parent=KTBS.filter)
        # it should just work, but we don't really care about the URI

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_method(id=meth.uri, parent=KTBS.filter)

    def test_create_two_methods(self):
        # check that independantly created methods have different URIs,
        # even if they have the same label
        met1 = self.base.create_method(parent=KTBS.filter,
                                       label="Duplicate label")
        met2 = self.base.create_method(parent=KTBS.filter,
                                       label="Duplicate label")
        eq_(met1.label, met2.label)
        assert met1.uri != met2.uri

    def test_create_bad_method(self):
        # ID not inside this base
        other_base = self.my_ktbs.create_base()
        wrong_uri = URIRef("WrongID", other_base.uri)
        with assert_raises(InvalidDataError):
            self.base.create_method(id=wrong_uri, parent=KTBS.filter)
        # wrong id
        with assert_raises(InvalidDataError):
            self.base.create_method(id="@WrongID", # invalid char @
                                          parent=KTBS.filter)
        with assert_raises(InvalidDataError):
            self.base.create_method(id="Wrong/ID", # invalid char /
                                          parent=KTBS.filter)
        # bad parameter name
        with assert_raises(ValueError):
            self.base.create_method(None, KTBS.filter, {"a=b": "c"})
        # bad parent method (in other base)
        other_base = self.my_ktbs.create_base()
        method = other_base.create_method(None, KTBS.filter, {"begin": "1000"})
        with assert_raises(InvalidDataError):
            self.base.create_method(None, method, {"end": "5000"})

    ######## add computed trace ########

    def test_create_computed_trace_no_id_no_label(self):
        ct = self.base.create_computed_trace(method=KTBS.external,
                                             parameters=FAKE_PARAMETERS)
        # it should just work, but we don't really care about the URI

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_computed_trace(id=ct.uri,
                                            method=KTBS.external,
                                            parameters=FAKE_PARAMETERS)

    def test_create_computed_trace_with_id(self):
        ct = self.base.create_computed_trace(id="ComputedTraceWithID/",
                                             method=KTBS.external,
                                             parameters=FAKE_PARAMETERS)
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/ComputedTraceWithID/")
        eq_(ct.get_uri(), generated_uri)

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_computed_trace(id="ComputedTraceWithID/",
                                            method=KTBS.external,
                                            parameters=FAKE_PARAMETERS)

    def test_create_computed_trace_with_label(self):
        ct = self.base.create_computed_trace(method=KTBS.external,
                                             parameters=FAKE_PARAMETERS,
                                             label="Computed trace with label")
        # it should just work, but we don't really care about the URI

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_computed_trace(id=ct.uri,
                                            method=KTBS.external,
                                            parameters=FAKE_PARAMETERS)

    def test_create_two_computed_traces(self):
        # check that independantly created computed traces have different URIs,
        # even if they have the same label
        ctr1 = self.base.create_computed_trace(method=KTBS.external,
                                               parameters=FAKE_PARAMETERS,
                                               label="Duplicate label")
        ctr2 = self.base.create_computed_trace(method=KTBS.external,
                                               parameters=FAKE_PARAMETERS,
                                               label="Duplicate label")
        eq_(ctr1.label, ctr2.label)
        assert ctr1.uri != ctr2.uri

    def test_create_bad_computed_trace(self):
        # ID not inside this base
        other_base = self.my_ktbs.create_base()
        wrong_uri = URIRef("WrongID", other_base.uri)
        with assert_raises(InvalidDataError):
            self.base.create_computed_trace(id=wrong_uri,
                                            method=KTBS.external,
                                            parameters=FAKE_PARAMETERS)
        # wrong id
        with assert_raises(InvalidDataError):
            self.base.create_computed_trace(id="WrongID", # no trailing slash
                                            method=KTBS.external,
                                            parameters=FAKE_PARAMETERS)
        with assert_raises(InvalidDataError):
            self.base.create_computed_trace(id="@WrongID/", # invalid char @
                                            method=KTBS.external,
                                            parameters=FAKE_PARAMETERS)
        with assert_raises(InvalidDataError):
            self.base.create_computed_trace(id="Wrong/ID", # invalid char /
                                            method=KTBS.external,
                                            parameters=FAKE_PARAMETERS)
        # no method
        with assert_raises(ValueError):
            self.base.create_computed_trace(id="ComputedTraceWithID/",
                                            parameters=FAKE_PARAMETERS)
                
    ######## remove base ########

    def test_remove_base(self):
        base_uri = self.base.get_uri()
        self.base.remove()
        eq_(self.my_ktbs.get_base(base_uri), None)


class TestKtbsBasePopulated(KtbsTestCase):

    def setUp(self):
        KtbsTestCase.setUp(self)
        self.base = self.my_ktbs.create_base(id="BaseTest/", label="Test base")
        self.model = self.base.create_model(id="ModelWithID",
                                            label="Test model")
        self.stored_trace = self.base.create_stored_trace(
                                          id="StoredTraceWithID/", 
                                          model=self.model,
                                          label="Test stored trace")
        self.method = self.base.create_method(id="MethodWithID",
                                              parent=KTBS.filter)
        self.computed_trace = \
            self.base.create_computed_trace(id="ComputedTraceWithID/",
                                            method=self.method,
                                            sources=[self.stored_trace])

    ######## get element information ########

    def test_list_models(self):
        lmod = self.base.list_models()
        eq_(lmod, [self.model])

    def test_get_model(self):
        mod = self.base.get("ModelWithID")
        eq_(mod, self.model)

    def test_list_traces(self):
        lt = self.base.list_traces()
        eq_(set(lt), set([self.stored_trace, self.computed_trace]))

    def test_get_stored_trace(self):
        st = self.base.get("StoredTraceWithID/")
        eq_(st, self.stored_trace)

    def test_get_computed_trace(self):
        st = self.base.get("ComputedTraceWithID/")
        eq_(st, self.computed_trace)

    def test_list_methods(self):
        lt = self.base.list_methods()
        eq_(lt, [self.method])

    def test_get_method(self):
        meth = self.base.get("MethodWithID")
        eq_(meth, self.method)

FAKE_PARAMETERS = {
    "command-line": "echo",
    "model":        "http://example.org/model",
    "origin":       "opaque-origin-12345",
}
