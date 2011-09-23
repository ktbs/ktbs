#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test KTBS client root API.
"""

import sys
from os.path import abspath, dirname, join

source_dir = dirname(dirname(abspath(__file__)))
lib_dir = join(source_dir, "lib")
sys.path.insert(0, lib_dir)

from ktbs.client.root import KtbsRoot
from ktbs.namespaces import KTBS, SKOS

from nose.tools import assert_raises
from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef
from rdfrest.exceptions import *

class TestKtbsRoot():
    def setUp(self):
        self.ktbs = KtbsRoot("http://localhost:8001/")

    def tearDown(self):
        self.ktbs = None

    def test_create_base_with_id(self):
        self.base = self.ktbs.create_base(id="base1/")
        print "test_create_base_with_id. Created base: %s, uri: %s" \
                                          % (self.base.label, self.base.uri)
        self.base.remove()

    def test_create_base_with_label(self):
        self.base = self.ktbs.create_base(label="base1")
        print "test_create_base_with_label. Created base: %s, uri: %s" \
                                          % (self.base.label, self.base.uri)
        self.base.remove()

    def test_create_base_with_id_and_label(self):
        self.base = self.ktbs.create_base(label="base1", id="base1/")
        print "test_create_base_with_id_and_label. Created base: %s, uri: %s" \
                                          % (self.base.label, self.base.uri)
        self.base.remove()

    def test_list_bases(self):
        self.base = self.ktbs.create_base(label="base1", id="base1/")
        rb = self.ktbs.bases
        if len(rb) == 0:
            print "No base in: %s" % self.ktbs.uri
        else:
            for b in rb:
                print "KTBSRoot base: %s, %s" % (b.label, b.uri)
            self.base.remove()

    def test_list_builtin_methods(self):
        rm = self.ktbs.builtin_methods
        if len(rm) == 0:
            print "No builtin method in: %s" % self.ktbs.uri
        else:
            for m in rm:
                print "KTBSRoot builtin method: %s" % m.label

if __name__ == '__main__':

    KR = TestKtbsRoot()
    KR.setUp()
    KR.test_create_base_with_id()
    KR.test_create_base_with_label()
    KR.test_create_base_with_id_and_label()
    KR.test_list_bases()
    KR.test_list_builtin_methods()
    KR.tearDown()
