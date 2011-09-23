#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test KTBS client base API.
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
 
MODEL_URI = "http://liris.cnrs.fr/silex/2011/simple-trace-model"
TRACE_ORIGIN = "1970-01-01T00:00:00Z"
OBSEL_TYPE = "SimpleObsel"

class TestKtbsBase():
    def setUp(self):
        self.ktbs = KtbsRoot("http://localhost:8001/")
        self.base = self.ktbs.create_base(label="base1", id="base1/")

    def tearDown(self):
        self.base.remove()
        self.base = None
        self.ktbs = None

    def test_get_uri(self):
        print self.base.uri

    def test_get_label(self):
        print self.base.label

    def test_set_label(self):
        self.base.label = "New name for base 1"
        print self.base.label

    def test_del_label(self):
        print self.base.del_label()

    def test_create_stored_trace(self):
        self.sto_t = self.base.create_stored_trace(
                model=MODEL_URI,
                origin=TRACE_ORIGIN,
                default_subject="Default testing subject",
                #label="Not implemented",
                id="t01/")
        print self.sto_t.uri

    def test_list_models(self):
        bm = self.base.models
        #bm = self.base.list_models()
        if len(bm) == 0:
            print "No models in: %s" % self.base.uri
        else:
            for m in bm:
                print "KTBSBase model: %s" % m.uri

if __name__ == '__main__':

    KB = TestKtbsBase()
    KB.setUp()
    KB.test_get_label()
    KB.test_set_label()
    KB.test_list_models()
    KB.tearDown()
