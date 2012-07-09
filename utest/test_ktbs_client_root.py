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
Nose unit-testing for the kTBS root client API.
"""
from unittest import TestCase, skip

from os.path import abspath, dirname, join
from subprocess import Popen, PIPE

from rdflib import URIRef

from ktbs.namespaces import KTBS

from ktbs.client.root import KtbsRoot

KTBS_ROOT = "http://localhost:8001/"

class TestKtbsClientRootGetInformation(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.baseb = cls.root.create_base(id="BaseWithID/")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_list_bases(self):
        lb = self.root.list_bases()
        assert len(lb) == 1

    def test_get_base(self):
        b = self.root.get_base(id="BaseWithID/")
        assert b.RDF_MAIN_TYPE == KTBS.Base

    def test_list_builtin_methods(self):
        for m in self.root.list_builtin_methods():
            print m.get_uri()

class TestKtbsClientRootAddElements(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_create_base_no_id_no_label(self):
        b = self.root.create_base()
        generated_uri = URIRef(KTBS_ROOT + "base/")
        assert b.get_uri() == generated_uri

    def test_create_base_with_id(self):
        b = self.root.create_base(id="BaseWithID/")
        generated_uri = URIRef(KTBS_ROOT + "BaseWithID/")
        assert b.get_uri() == generated_uri

    def test_create_base_with_label(self):
        b = self.root.create_base(label="Base with label")
        generated_uri = URIRef(KTBS_ROOT + "base-with-label/")
        assert b.get_uri() == generated_uri

    def test_create_base_with_id_and_label(self):
        b = self.root.create_base(id="BaseWithIDAndLabel/", label="Base with ID and label")
        generated_uri = URIRef(KTBS_ROOT + "BaseWithIDAndLabel/")
        assert b.get_uri() == generated_uri
