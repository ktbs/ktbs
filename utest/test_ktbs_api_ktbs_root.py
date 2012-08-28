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
Nose unit-testing for the kTBS root client API.
"""
from unittest import TestCase, skip
from nose.tools import assert_raises, eq_

from rdflib import BNode, Graph, RDF, URIRef
from rdfrest.exceptions import InvalidDataError, RdfRestException

from ktbs.namespace import KTBS

from .test_ktbs_engine import KtbsTestCase

KTBS_ROOT = "http://localhost:12345/"

class TestKtbsRoot(KtbsTestCase):

    ######## get information ########

    def test_list_bases(self):
        base = self.my_ktbs.create_base()
        lb = self.my_ktbs.list_bases()
        eq_(lb, [base])

    def test_get_base(self):
        bas1 = self.my_ktbs.create_base("BaseWithID/")
        bas2 = self.my_ktbs.get_base(id="BaseWithID/")
        eq_(bas1, bas2)

    def test_list_builtin_methods(self):
        for m in self.my_ktbs.list_builtin_methods():
            print m.uri

    ######## add base ########

    def test_create_base_no_id_no_label(self):
        b = self.my_ktbs.create_base()
        # it should just work, but we don't really care about the URI

        # check duplicate URI
        with assert_raises(InvalidDataError):
            b = self.my_ktbs.create_base(id=b.uri)

    def test_create_base_with_id(self):
        b = self.my_ktbs.create_base(id="BaseWithID/")
        generated_uri = URIRef(KTBS_ROOT + "BaseWithID/")
        eq_(b.get_uri(), generated_uri)

        # check duplicate URI
        with assert_raises(InvalidDataError):
            b = self.my_ktbs.create_base(id="BaseWithID/")

    def test_create_base_with_label(self):
        b = self.my_ktbs.create_base(label="Base with label")
        # it should just work, but we don't really care about the URI

        # check duplicate URI
        with assert_raises(InvalidDataError):
            b = self.my_ktbs.create_base(id=b.uri)

    def test_create_base_with_id_and_label(self):
        b = self.my_ktbs.create_base(id="BaseWithIDAndLabel/",
                                     label="Base with ID and label")
        generated_uri = URIRef(KTBS_ROOT + "BaseWithIDAndLabel/")
        eq_(b.get_uri(), generated_uri)

    def test_create_two_bases(self):
        # check that independantly created bases have different URIs,
        # even if they have the same label
        bas1 = self.my_ktbs.create_base(label="Duplicate label")
        bas2 = self.my_ktbs.create_base(label="Duplicate label")
        eq_(bas1.label, bas2.label)
        assert bas1.uri != bas2.uri

    def test_create_bad_base(self):
        # wrong id - not in this kTBS
        with assert_raises(RdfRestException):
            self.my_ktbs.create_base(id="http://example.org/base/")
        # wrong id - invalid characters
        with assert_raises(RdfRestException):
            self.my_ktbs.create_base(id="@foo")
        with assert_raises(RdfRestException):
            self.my_ktbs.create_base(id="foo/bar")
        # wrong id - no slash
        with assert_raises(RdfRestException):
            self.my_ktbs.create_base(id="WrongID") # no slash
