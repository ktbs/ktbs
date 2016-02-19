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

from json import dumps, loads
from nose.tools import assert_set_equal, eq_, raises
from rdflib import Literal
from unittest import skip

from ktbs.engine.resource import METADATA
from ktbs.methods.fsa import LOG as FSA_LOG
from ktbs.namespace import KTBS, KTBS_NS_URI

from .test_ktbs_engine import KtbsTestCase

def get_custom_state(computed_trace, key=None):
        jsonstr = computed_trace.metadata.value(computed_trace.uri,
                                                METADATA.computation_state)
        jsonobj = loads(jsonstr)
        ret = jsonobj.get('custom')
        if ret is not None and key is not None:
            ret = ret.get(key)
        return ret

def assert_obsel_type(obsel, obsel_type):
    eq_(obsel.obsel_type.uri, obsel_type.uri)

def assert_source_obsels(obsel, source_obsels):
    assert_set_equal(set(obsel.iter_source_obsels()), set(source_obsels))




class TestFSA(KtbsTestCase):

    def setUp(self):
        KtbsTestCase.setUp(self)
        self.log = FSA_LOG
        self.base = self.my_ktbs.create_base("b/")
        self.model_src = self.base.create_model("ms")
        self.otypeA = self.model_src.create_obsel_type("#otA")
        self.otypeB = self.model_src.create_obsel_type("#otB")
        self.otypeC = self.model_src.create_obsel_type("#otC")
        self.otypeD = self.model_src.create_obsel_type("#otD")
        self.otypeE = self.model_src.create_obsel_type("#otE")
        self.model_dst = self.base.create_model("md")
        self.otypeX = self.model_dst.create_obsel_type("#otX")
        self.otypeY = self.model_dst.create_obsel_type("#otY")
        self.otypeZ = self.model_dst.create_obsel_type("#otZ")
        self.base_structure = {
            "states": {
                "start": {
                    "transitions": [
                        {
                            "condition": self.otypeA.uri,
                            "target": "s1"
                        },
                        {
                            "condition": "#otA",
                            "target": "s2"
                        },
                        {
                            "condition": self.otypeE.uri,
                            "target": "s3"
                        },
                    ]
                },
                "s1": {
                    "max_noise": 1,
                    "transitions": [
                        {
                            "condition": self.otypeB.uri,
                            "target": "s1"
                        },
                        {
                            "condition": "#otC",
                            "target": self.otypeX.uri,
                        },
                    ]
                },
                "s2": {
                    "max_noise": 1,
                    "transitions": [
                        {
                            "condition": self.otypeC.uri,
                            "target": "s2"
                        },
                        {
                            "condition": self.otypeD.uri,
                            "target": "#otY",
                        },
                    ]
                },
                "s3": {
                    "max_noise": 1,
                    "transitions": [
                        {
                            "condition": self.otypeD.uri,
                            "target": "#otZ"
                        },
                    ]
                },
                self.otypeX.uri: {
                    "terminal": True,
                },
                "#otY": {
                    "terminal": True,
                },
                "#otZ": {
                    "terminal": True,
                },
            }
        }
        self.src = self.base.create_stored_trace("s/", self.model_src, default_subject="alice")

    def test_base_structure(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA = self.src.create_obsel("oA", self.otypeA, 0)
        eq_(len(ctr.obsels), 0)
        oB = self.src.create_obsel("oB", self.otypeB, 1)
        eq_(len(ctr.obsels), 0)
        oC = self.src.create_obsel("oC", self.otypeC, 2)
        eq_(len(ctr.obsels), 1)
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA, oB, oC])
        oD = self.src.create_obsel("oD", self.otypeD, 3)
        eq_(len(ctr.obsels), 1) # no overlap, so no new obsel

    def test_allow_overlap(self):
        self.base_structure['allow_overlap'] = True
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA = self.src.create_obsel("oA", self.otypeA, 0)
        eq_(len(ctr.obsels), 0)
        oB = self.src.create_obsel("oB", self.otypeB, 1)
        eq_(len(ctr.obsels), 0)
        oC = self.src.create_obsel("oC", self.otypeC, 2)
        eq_(len(ctr.obsels), 1)
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA, oB, oC])
        oD = self.src.create_obsel("oD", self.otypeD, 3)
        eq_(len(ctr.obsels), 2)
        assert_obsel_type(ctr.obsels[1], self.otypeY)
        assert_source_obsels(ctr.obsels[1], [oA, oC, oD])

    def test_simultaneaous_matches(self):
        self.base_structure['allow_overlap'] = True
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA = self.src.create_obsel("oA", self.otypeA, 0)
        eq_(len(ctr.obsels), 0)
        oE = self.src.create_obsel("oE", self.otypeE, 1)
        eq_(len(ctr.obsels), 0)
        oD = self.src.create_obsel("oD", self.otypeD, 2)
        eq_(len(ctr.obsels), 2)
        assert_set_equal(set([self.otypeY.uri, self.otypeZ.uri ]), set(
            obs.obsel_type.uri for obs in ctr.obsels
        ))

class TestFSAAsk(KtbsTestCase):

    def setUp(self):
        KtbsTestCase.setUp(self)
        self.log = FSA_LOG
        self.base = self.my_ktbs.create_base("b/")
        self.model_src = self.base.create_model("ms")
        self.otypeA = self.model_src.create_obsel_type("#otA")
        self.atypeV = self.model_src.create_attribute_type("#atV")
        self.otypeB = self.model_src.create_obsel_type("#otB")
        self.atypeW = self.model_src.create_attribute_type("#atW")
        self.otypeC = self.model_src.create_obsel_type("#otC")
        self.model_dst = self.base.create_model("md")
        self.otypeX = self.model_dst.create_obsel_type("#otX")
        self.otypeY = self.model_dst.create_obsel_type("#otY")
        self.otypeZ = self.model_dst.create_obsel_type("#otZ")
        self.base_structure = {
            "states": {
                "start": {
                    "transitions": [
                        {
                            "condition": self.otypeA.uri,
                            "target": "s1"
                        },
                        {
                            "condition": self.otypeB.uri,
                            "target": "s2"
                        },
                        {
                            "condition": self.otypeC.uri,
                            "target": "s3"
                        },
                    ]
                },
                "s1": {
                    "transitions": [
                        {
                            "condition": '?obs m:atV 42',
                            "matcher": "sparql-ask",
                            "target": self.otypeX.uri,
                        },
                        {
                            "condition": "?obs m:atV ?v . FILTER(?v > 42)",
                            "matcher": "sparql-ask",
                            "target": self.otypeY.uri,
                        },
                    ]
                },
                "s2": {
                    "max_noise": 1,
                    "transitions": [
                        {
                            "condition": "?obs m:atW ?any",
                            "matcher": "sparql-ask",
                            "target": self.otypeZ.uri,
                        },
                    ]
                },
                "s3": {
                    "transitions": [
                        {
                            "condition": "?obs m:atV ?val. ?pred m:atV ?val",
                            "matcher": "sparql-ask",
                            "target": self.otypeX.uri,
                        },
                    ]
                },
                self.otypeX.uri: {
                    "terminal": True,
                },
                self.otypeY.uri: {
                    "terminal": True,
                },
                self.otypeZ.uri: {
                    "terminal": True,
                },
            }
        }
        self.src = self.base.create_stored_trace("s/", self.model_src, default_subject="alice")

    def test_X_with_AA(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA1 = self.src.create_obsel("oA1", self.otypeA, 0, attributes={self.atypeV: Literal(41)})
        eq_(len(ctr.obsels), 0)
        oA2 = self.src.create_obsel("oA2", self.otypeA, 1, attributes={self.atypeV: Literal(42)})
        eq_(len(ctr.obsels), 1)
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA1, oA2])

    def test_X_with_AB(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA1 = self.src.create_obsel("oA1", self.otypeA, 0, attributes={self.atypeV: Literal(41)})
        eq_(len(ctr.obsels), 0)
        oB2 = self.src.create_obsel("oB2", self.otypeB, 1, attributes={self.atypeV: Literal(42)})
        eq_(len(ctr.obsels), 1)
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA1, oB2])

    def test_Y(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA1 = self.src.create_obsel("oA1", self.otypeA, 0, attributes={self.atypeV: Literal(41)})
        eq_(len(ctr.obsels), 0)
        oA2 = self.src.create_obsel("oA2", self.otypeA, 1, attributes={self.atypeV: Literal(43)})
        eq_(len(ctr.obsels), 1)
        assert_obsel_type(ctr.obsels[0], self.otypeY)
        assert_source_obsels(ctr.obsels[0], [oA1, oA2])

    def test_no_match_V(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA1 = self.src.create_obsel("oA1", self.otypeA, 0, attributes={self.atypeV: Literal(42)})
        eq_(len(ctr.obsels), 0)
        oA2 = self.src.create_obsel("oA2", self.otypeA, 1, attributes={self.atypeV: Literal(41)})
        eq_(len(ctr.obsels), 0)

    def test_pred(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oC1 = self.src.create_obsel("oC1", self.otypeC, 0, attributes={self.atypeV: Literal(41)})
        eq_(len(ctr.obsels), 0)
        oC2 = self.src.create_obsel("oC2", self.otypeC, 1, attributes={self.atypeV: Literal(42)})
        eq_(len(ctr.obsels), 0)
        oC3 = self.src.create_obsel("oC3", self.otypeC, 2, attributes={self.atypeV: Literal(42)})
        eq_(len(ctr.obsels), 1)
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oC2, oC3])
