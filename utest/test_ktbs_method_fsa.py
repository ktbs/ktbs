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
from unittest import skip

import pytest
from fsa4streams.fsa import FSA
from json import dumps, loads
from rdflib import Literal, XSD

from ktbs.engine.resource import METADATA
from ktbs.methods.fsa import LOG as FSA_LOG
from ktbs.namespace import KTBS, KTBS_NS_URI
from rdfrest.exceptions import CanNotProceedError

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
    assert obsel.obsel_type.uri == obsel_type.uri

def assert_source_obsels(obsel, source_obsels):
    assert set(obsel.iter_source_obsels()) == set(source_obsels)


class TestFSA(KtbsTestCase):

    def setup_method(self):
        KtbsTestCase.setup_method(self)
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

    def test_missing_parameter(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"model": self.model_dst.uri,},
                                         [self.src],)
        with pytest.raises(CanNotProceedError):
            ctr.obsel_collection.force_state_refresh()
        assert ctr.diagnosis is not None

    def test_base_structure(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA = self.src.create_obsel("oA", self.otypeA, 0)
        assert len(ctr.obsels) == 0
        oB = self.src.create_obsel("oB", self.otypeB, 1)
        assert len(ctr.obsels) == 0
        oC = self.src.create_obsel("oC", self.otypeC, 2)
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA, oB, oC])
        oD = self.src.create_obsel("oD", self.otypeD, 3)
        assert len(ctr.obsels) == 1 # no overlap, so no new obsel

    def test_allow_overlap(self):
        self.base_structure['allow_overlap'] = True
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA = self.src.create_obsel("oA", self.otypeA, 0)
        assert len(ctr.obsels) == 0
        oB = self.src.create_obsel("oB", self.otypeB, 1)
        assert len(ctr.obsels) == 0
        oC = self.src.create_obsel("oC", self.otypeC, 2)
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA, oB, oC])
        oD = self.src.create_obsel("oD", self.otypeD, 3)
        assert len(ctr.obsels) == 2
        assert_obsel_type(ctr.obsels[1], self.otypeY)
        assert_source_obsels(ctr.obsels[1], [oA, oC, oD])

    def test_simultaneaous_matches(self):
        self.base_structure['allow_overlap'] = True
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA = self.src.create_obsel("oA", self.otypeA, 0)
        assert len(ctr.obsels) == 0
        oE = self.src.create_obsel("oE", self.otypeE, 1)
        assert len(ctr.obsels) == 0
        oD = self.src.create_obsel("oD", self.otypeD, 2)
        assert len(ctr.obsels) == 2
        assert set([self.otypeY.uri, self.otypeZ.uri ]) == set(
            obs.obsel_type.uri for obs in ctr.obsels
        )

class TestFSAAsk(KtbsTestCase):

    def setup_method(self):
        KtbsTestCase.setup_method(self)
        self.log = FSA_LOG
        self.base = self.my_ktbs.create_base("b/")
        self.model_src = self.base.create_model("ms")
        self.otypeA = self.model_src.create_obsel_type("#otA")
        self.atypeV = self.model_src.create_attribute_type("#atV")
        self.otypeB = self.model_src.create_obsel_type("#otB")
        self.atypeW = self.model_src.create_attribute_type("#atW")
        self.otypeC = self.model_src.create_obsel_type("#otC")
        self.otypeD = self.model_src.create_obsel_type("#otD")
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
                        {
                            "condition": self.otypeD.uri,
                            "target": "s4"
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
                "s4": {
                    "transitions": [
                        {
                            "condition": "?obs a m:otD; m:atV ?val."
                                         "?first m:atV ?valf."
                                         "FILTER(?valf < ?val)",
                            "matcher": "sparql-ask",
                            "target": "s4",
                        },
                        {
                            "condition": self.otypeA.uri,
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
        assert len(ctr.obsels) == 0
        oA2 = self.src.create_obsel("oA2", self.otypeA, 1, attributes={self.atypeV: Literal(42)})
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA1, oA2])

    def test_X_with_AB(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA1 = self.src.create_obsel("oA1", self.otypeA, 0, attributes={self.atypeV: Literal(41)})
        assert len(ctr.obsels) == 0
        oB2 = self.src.create_obsel("oB2", self.otypeB, 1, attributes={self.atypeV: Literal(42)})
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA1, oB2])

    def test_Y(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA1 = self.src.create_obsel("oA1", self.otypeA, 0, attributes={self.atypeV: Literal(41)})
        assert len(ctr.obsels) == 0
        oA2 = self.src.create_obsel("oA2", self.otypeA, 1, attributes={self.atypeV: Literal(43)})
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[0], self.otypeY)
        assert_source_obsels(ctr.obsels[0], [oA1, oA2])

    def test_no_match_V(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA1 = self.src.create_obsel("oA1", self.otypeA, 0, attributes={self.atypeV: Literal(42)})
        assert len(ctr.obsels) == 0
        oA2 = self.src.create_obsel("oA2", self.otypeA, 1, attributes={self.atypeV: Literal(41)})
        assert len(ctr.obsels) == 0

    def test_pred(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oC1 = self.src.create_obsel("oC1", self.otypeC, 0, attributes={self.atypeV: Literal(41)})
        assert len(ctr.obsels) == 0
        oC2 = self.src.create_obsel("oC2", self.otypeC, 1, attributes={self.atypeV: Literal(42)})
        assert len(ctr.obsels) == 0
        oC3 = self.src.create_obsel("oC3", self.otypeC, 2, attributes={self.atypeV: Literal(42)})
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oC2, oC3])

    def test_first(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oD1 = self.src.create_obsel("oD1", self.otypeD, 0, attributes={self.atypeV: Literal(2)})
        assert len(ctr.obsels) == 0
        oD2 = self.src.create_obsel("oD2", self.otypeD, 1, attributes={self.atypeV: Literal(1)})
        assert len(ctr.obsels) == 0
        oD3 = self.src.create_obsel("oD3", self.otypeD, 2, attributes={self.atypeV: Literal(4)})
        assert len(ctr.obsels) == 0
        oD4 = self.src.create_obsel("oD4", self.otypeD, 3, attributes={self.atypeV: Literal(3)})
        assert len(ctr.obsels) == 0
        oA1 = self.src.create_obsel("oA1", self.otypeA, 4)
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oD2, oD3, oD4, oA1])

class TestFSAMaxDuration(KtbsTestCase):

    def setup_method(self):
        KtbsTestCase.setup_method(self)
        self.log = FSA_LOG
        self.base = self.my_ktbs.create_base("b/")
        self.model_src = self.base.create_model("ms")
        self.otypeA = self.model_src.create_obsel_type("#otA")
        self.otypeB = self.model_src.create_obsel_type("#otB")
        self.model_dst = self.base.create_model("md")
        self.otypeX = self.model_dst.create_obsel_type("#otX")
        self.otypeY = self.model_dst.create_obsel_type("#otY")
        self.src = self.base.create_stored_trace("s/", self.model_src, default_subject="alice")

        fsa = FSA.make_empty()
        (fsa.add_state("start")
               .add_transition("#otA", "#otX")
            .add_state("#otX", terminal=True, max_duration=1, max_total_duration=4)
                .add_transition("#otB", "#otX"))
        self.base_structure = fsa.export_structure_as_dict()

    def test_exceed_max_duration(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA0 = self.src.create_obsel("oA0", self.otypeA, 0)
        assert len(ctr.obsels) == 0
        oB1 = self.src.create_obsel("oB1", self.otypeB, 1)
        assert len(ctr.obsels) == 0
        oB3 = self.src.create_obsel("oB3", self.otypeB, 3)
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA0, oB1])

    def test_exceed_max_total_duration(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA0 = self.src.create_obsel("oA0", self.otypeA, 0)
        assert len(ctr.obsels) == 0
        oB1 = self.src.create_obsel("oB1", self.otypeB, 1)
        assert len(ctr.obsels) == 0
        oB2 = self.src.create_obsel("oB2", self.otypeB, 2)
        assert len(ctr.obsels) == 0
        oB3 = self.src.create_obsel("oB3", self.otypeB, 3)
        assert len(ctr.obsels) == 0
        oB4 = self.src.create_obsel("oB4", self.otypeB, 4)
        assert len(ctr.obsels) == 0
        oB5 = self.src.create_obsel("oB5", self.otypeB, 5)
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA0, oB1, oB2, oB3, oB4])

class TestFSAKtbsSpecificProperties(KtbsTestCase):

    def setup_method(self):
        KtbsTestCase.setup_method(self)
        self.log = FSA_LOG
        self.base = self.my_ktbs.create_base("b/")
        self.model_src = self.base.create_model("ms")
        self.otypeA = self.model_src.create_obsel_type("#otA")
        self.otypeB = self.model_src.create_obsel_type("#otB")
        self.otypeC = self.model_src.create_obsel_type("#otC")
        self.otypeD = self.model_src.create_obsel_type("#otD")
        self.otypeE = self.model_src.create_obsel_type("#otE")
        self.otypeF = self.model_src.create_obsel_type("#otF")
        self.atypeV = self.model_src.create_attribute_type("#atV")
        self.atypeW = self.model_src.create_attribute_type("#atW")
        self.model_dst = self.base.create_model("md")
        self.otypeX = self.model_dst.create_obsel_type("#otX")
        self.otypeY = self.model_dst.create_obsel_type("#otY")
        self.atype1 = self.model_dst.create_attribute_type("#at1")
        self.atype2 = self.model_dst.create_attribute_type("#at2")
        self.atypeFirst = self.model_dst.create_attribute_type("#atFirst")
        self.atypeLast = self.model_dst.create_attribute_type("#atLast")
        self.atypeCount = self.model_dst.create_attribute_type("#atCount")
        self.atypeSum = self.model_dst.create_attribute_type("#atSum")
        self.atypeAvg = self.model_dst.create_attribute_type("#atAvg")
        self.atypeMin = self.model_dst.create_attribute_type("#atMin")
        self.atypeMax = self.model_dst.create_attribute_type("#atMax")
        self.atypeSpan = self.model_dst.create_attribute_type("#atSpan")
        self.atypeConcat = self.model_dst.create_attribute_type("#atConcat")
        self.src = self.base.create_stored_trace("s/", self.model_src, default_subject="alice")

        self.base_structure = {
            "states": {
                "start": {
                    "transitions": [
                        {
                            "condition": "#otA",
                            "target": "terminalA"
                        },
                        {
                            "condition": "#otB",
                            "target": "terminalB"
                        },
                        {
                            "condition": "#otC",
                            "target": "terminalC"
                        },
                        {
                            "condition": "#otE",
                            "target": "s1"
                        },
                    ]
                },
                "terminalA": {
                    "terminal": True,
                    "ktbs_obsel_type": "#otX",
                    "ktbs_attributes": {
                        "#at1": "#atV",
                        "#at2": "#atW"
                    },
                    "transitions": [
                        {
                            "condition": "#otA",
                            "target": "terminalA"
                        }
                    ]
                },
                "terminalB": {
                    "terminal": True,
                    "ktbs_obsel_type": "#otX",
                    "transitions": [
                        {
                            "condition": "#otB",
                            "target": "terminalB"
                        }
                    ]
                },
                "terminalC": {
                    "terminal": True,
                    "ktbs_obsel_type": "#otX",
                    "ktbs_attributes": {
                        "#atFirst": "first #atV",
                        "#atLast": "last #atV",
                        "#atCount": "count #atV",
                        "#atSum": "sum #atV",
                        "#atAvg": "avg #atV",
                        "#atMin": "min #atV",
                        "#atMax": "max #atV",
                        "#atSpan": "span #atV",
                        "#atConcat": "concat #atV"
                    },
                    "transitions": [
                        {
                            "condition": "#otC",
                            "target": "terminalC"
                        }
                    ]
                },
                "s1": {
                    "max_noise": 10,
                    "transitions": [
                        {
                            "condition": "#otE",
                            "target": "terminalE",
                        },
                        {
                            "condition": "#otF",
                            "target": "break",
                        },
                    ]
                },
                "terminalE": {
                    "terminal": True,
                    "ktbs_obsel_type": "#otX",
                },
                "break": {
                    "terminal": True,
                    "ktbs_obsel_type": None,
                },
            }
        }

    def test_obsel_type(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA0 = self.src.create_obsel("oA0", self.otypeA, 0)
        assert len(ctr.obsels) == 0
        oB1 = self.src.create_obsel("oB1", self.otypeB, 1)
        assert len(ctr.obsels) == 1
        oB2 = self.src.create_obsel("oB2", self.otypeB, 2)
        assert len(ctr.obsels) == 1
        oA3 = self.src.create_obsel("oA3", self.otypeA, 3)
        assert len(ctr.obsels) == 2
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_obsel_type(ctr.obsels[1], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA0])
        assert_source_obsels(ctr.obsels[1], [oB1, oB2])


    def test_attributes(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oA0 = self.src.create_obsel("oA0", self.otypeA, 0,
                                    attributes={self.atypeV: Literal(39),
                                                self.atypeW: Literal(40)})
        assert len(ctr.obsels) == 0
        oA1 = self.src.create_obsel("oA1", self.otypeA, 1,
                                    attributes={self.atypeV: Literal(41)})
        assert len(ctr.obsels) == 0
        oA2 = self.src.create_obsel("oA2", self.otypeA, 2,
                                    attributes={self.atypeW: Literal(42)})
        assert len(ctr.obsels) == 0
        oB3 = self.src.create_obsel("oB3", self.otypeB, 3,
                                    attributes={self.atypeV: Literal(43)})
        assert len(ctr.obsels) == 1
        oB4 = self.src.create_obsel("oB4", self.otypeB, 4,
                                    attributes={self.atypeW: Literal(44)})
        assert len(ctr.obsels) == 1
        oA5 = self.src.create_obsel("oA5", self.otypeA, 5,
                                    attributes={self.atypeV: Literal(45)})
        assert len(ctr.obsels) == 2
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_obsel_type(ctr.obsels[1], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oA0, oA1, oA2])
        assert_source_obsels(ctr.obsels[1], [oB3, oB4])
        assert ctr.obsels[0].get_attribute_value(self.atype1) == 41
        assert ctr.obsels[0].get_attribute_value(self.atype2) == 42
        assert ctr.obsels[1].get_attribute_value(self.atype1) == None
        assert ctr.obsels[1].get_attribute_value(self.atype2) == None

    def test_aggregate_functions(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oC0 = self.src.create_obsel("oC0", self.otypeC, 0)
        assert len(ctr.obsels) == 0
        oC1 = self.src.create_obsel("oC1", self.otypeC, 1)
        assert len(ctr.obsels) == 0
        oD2 = self.src.create_obsel("oD2", self.otypeD, 2)
        assert len(ctr.obsels) == 1
        assert_source_obsels(ctr.obsels[-1], [oC0, oC1])
        assert ctr.obsels[-1].get_attribute_value(self.atypeFirst) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeLast) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeCount) == 0
        assert ctr.obsels[-1].get_attribute_value(self.atypeSum) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeAvg) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeMin) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeMax) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeSpan) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeConcat) == None

        oC3 = self.src.create_obsel("oC3", self.otypeC, 3)
        assert len(ctr.obsels) == 1
        oC4 = self.src.create_obsel("oC4", self.otypeC, 4,
                                    attributes={self.atypeV: Literal(9)})
        assert len(ctr.obsels) == 1
        oC5 = self.src.create_obsel("oC5", self.otypeC, 5)
        assert len(ctr.obsels) == 1
        oC6 = self.src.create_obsel("oC6", self.otypeC, 6,
                                    attributes={self.atypeV: Literal(11)})
        assert len(ctr.obsels) == 1
        oC7 = self.src.create_obsel("oC7", self.otypeC, 7,
                                    attributes={self.atypeV: Literal(5)})
        assert len(ctr.obsels) == 1
        oC8 = self.src.create_obsel("oC8", self.otypeC, 8)
        assert len(ctr.obsels) == 1
        oD9 = self.src.create_obsel("oD9", self.otypeD, 9)
        assert len(ctr.obsels) == 2
        assert_source_obsels(ctr.obsels[-1], [oC3, oC4, oC5, oC6, oC7, oC8])

        assert ctr.obsels[-1].get_attribute_value(self.atypeFirst) == 9
        assert ctr.obsels[-1].get_attribute_value(self.atypeLast) == 5
        assert ctr.obsels[-1].get_attribute_value(self.atypeCount) == 3
        assert ctr.obsels[-1].get_attribute_value(self.atypeSum) == 25
        assert ctr.obsels[-1].get_attribute_value(self.atypeAvg) == 25.0/3
        assert ctr.obsels[-1].get_attribute_value(self.atypeMin) == 5
        assert ctr.obsels[-1].get_attribute_value(self.atypeMax) == 11
        assert ctr.obsels[-1].get_attribute_value(self.atypeSpan) == 6
        assert ctr.obsels[-1].get_attribute_value(self.atypeConcat) == "9 11 5"

    def test_aggregate_functions_heterogeneous_numeric(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oC0 = self.src.create_obsel("oC0", self.otypeC, 0)
        assert len(ctr.obsels) == 0
        oC1 = self.src.create_obsel("oC1", self.otypeC, 1)
        assert len(ctr.obsels) == 0
        oD2 = self.src.create_obsel("oD2", self.otypeD, 2)
        assert len(ctr.obsels) == 1
        assert_source_obsels(ctr.obsels[-1], [oC0, oC1])
        assert ctr.obsels[-1].get_attribute_value(self.atypeFirst) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeLast) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeCount) == 0
        assert ctr.obsels[-1].get_attribute_value(self.atypeSum) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeAvg) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeMin) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeMax) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeSpan) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeConcat) == None

        oC3 = self.src.create_obsel("oC3", self.otypeC, 3)
        assert len(ctr.obsels) == 1
        oC4 = self.src.create_obsel(
                "oC4", self.otypeC, 4,
                attributes={self.atypeV: Literal(9)})
        assert len(ctr.obsels) == 1
        oC5 = self.src.create_obsel("oC5", self.otypeC, 5)
        assert len(ctr.obsels) == 1
        oC6 = self.src.create_obsel(
                "oC6", self.otypeC, 6,
                attributes={self.atypeV: Literal(11.0)})
        assert len(ctr.obsels) == 1
        oC7 = self.src.create_obsel(
                "oC7", self.otypeC, 7,
                attributes={self.atypeV: Literal("5", datatype=XSD.decimal)})
        assert len(ctr.obsels) == 1
        oC8 = self.src.create_obsel("oC8", self.otypeC, 8)
        assert len(ctr.obsels) == 1
        oD9 = self.src.create_obsel("oD9", self.otypeD, 9)
        assert len(ctr.obsels) == 2
        assert_source_obsels(ctr.obsels[-1], [oC3, oC4, oC5, oC6, oC7, oC8])

        assert ctr.obsels[-1].get_attribute_value(self.atypeFirst) == 9
        assert ctr.obsels[-1].get_attribute_value(self.atypeLast) == 5
        assert ctr.obsels[-1].get_attribute_value(self.atypeCount) == 3
        assert ctr.obsels[-1].get_attribute_value(self.atypeSum) == 25
        assert ctr.obsels[-1].get_attribute_value(self.atypeAvg) == 25.0/3
        assert ctr.obsels[-1].get_attribute_value(self.atypeMin) == 5
        assert ctr.obsels[-1].get_attribute_value(self.atypeMax) == 11
        assert ctr.obsels[-1].get_attribute_value(self.atypeSpan) == 6
        assert ctr.obsels[-1].get_attribute_value(self.atypeConcat) == "9 11.0 5"


    def test_aggregate_functions_heterogeneous(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oC3 = self.src.create_obsel("oC3", self.otypeC, 3)
        assert len(ctr.obsels) == 0
        oC4 = self.src.create_obsel("oC4", self.otypeC, 4,
                                    attributes={self.atypeV: Literal(42)})
        assert len(ctr.obsels) == 0
        oC5 = self.src.create_obsel("oC5", self.otypeC, 5)
        assert len(ctr.obsels) == 0
        oC6 = self.src.create_obsel("oC6", self.otypeC, 6,
                                    attributes={self.atypeV: Literal("foo")})
        assert len(ctr.obsels) == 0
        oC7 = self.src.create_obsel("oC7", self.otypeC, 7)
        assert len(ctr.obsels) == 0
        oC8 = self.src.create_obsel("oC8", self.otypeC, 8)
        assert len(ctr.obsels) == 0
        oD9 = self.src.create_obsel("oD9", self.otypeD, 9)
        assert len(ctr.obsels) == 1
        assert_source_obsels(ctr.obsels[-1], [oC3, oC4, oC5, oC6, oC7, oC8])

        assert ctr.obsels[-1].get_attribute_value(self.atypeFirst) == 42
        assert ctr.obsels[-1].get_attribute_value(self.atypeLast) == "foo"
        assert ctr.obsels[-1].get_attribute_value(self.atypeCount) == 2
        assert ctr.obsels[-1].get_attribute_value(self.atypeSum) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeAvg) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeMin) == 42
        assert ctr.obsels[-1].get_attribute_value(self.atypeMax) == "foo"
        assert ctr.obsels[-1].get_attribute_value(self.atypeSpan) == None
        assert ctr.obsels[-1].get_attribute_value(self.atypeConcat) == "42 foo"

    def est_obsel_type(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.fsa,
                                         {"fsa": dumps(self.base_structure),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oE0 = self.src.create_obsel("oE0", self.otypeE, 0)
        assert len(ctr.obsels) == 0
        oD1 = self.src.create_obsel("oD1", self.otypeD, 1)
        assert len(ctr.obsels) == 0
        oE2 = self.src.create_obsel("oE2", self.otypeE, 2)
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[0], self.otypeX)
        assert_source_obsels(ctr.obsels[0], [oE0, oD1, oE2])

        # but this sequences "breaks" with oF4,
        # and generates no obsel (ktbs_obsel_type is null)
        oE3 = self.src.create_obsel("oE3", self.otypeE, 3)
        assert len(ctr.obsels) == 1
        oF4 = self.src.create_obsel("oF4", self.otypeF, 4)
        assert len(ctr.obsels) == 1
        oE5 = self.src.create_obsel("oE5", self.otypeE, 5)
        assert len(ctr.obsels) == 1
