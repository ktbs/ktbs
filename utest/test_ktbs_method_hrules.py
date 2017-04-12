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
from ktbs.methods.hrules import LOG as HRULES_LOG
from ktbs.namespace import KTBS, KTBS_NS_URI
from rdfrest.exceptions import CanNotProceedError

from .test_ktbs_engine import KtbsTestCase

def assert_obsel_type(obsel, obsel_type):
    assert obsel.obsel_type.uri == obsel_type.uri

def assert_source_obsels(obsel, source_obsels):
    assert set(obsel.iter_source_obsels()) == set(source_obsels)

import logging
logging.basicConfig()


class TestHRules(KtbsTestCase):

    def setup(self):
        KtbsTestCase.setup(self)
        self.log = HRULES_LOG
        self.base = self.my_ktbs.create_base("b/")
        self.model_src = self.base.create_model("ms")
        self.otypeA = self.model_src.create_obsel_type("#otA")
        self.otypeB = self.model_src.create_obsel_type("#otB")
        self.otypeC = self.model_src.create_obsel_type("#otC")
        self.otypeD = self.model_src.create_obsel_type("#otD")
        self.otypeE = self.model_src.create_obsel_type("#otE")
        self.atypeV = self.model_src.create_obsel_type("#atV")
        self.atypeW = self.model_src.create_obsel_type("#atW")
        self.model_dst = self.base.create_model("md")
        self.otypeX = self.model_dst.create_obsel_type("#otX")
        self.otypeY = self.model_dst.create_obsel_type("#otY")
        self.otypeZ = self.model_dst.create_obsel_type("#otZ")
        self.base_rules = [
            {
                'id': self.otypeX.uri,
                'visible': True,
                'rules': [
                    {
                        'type': self.otypeA.uri,
                    },
                    {
                        'type': self.otypeB.uri,
                        'attributes': [
                            {
                                'uri': self.atypeV.uri,
                                'operator': '==',
                                'value': '0',
                            },
                        ],
                    },
                    {
                        'attributes': [
                            {
                                'uri': self.atypeV.uri,
                                'operator': '>',
                                'value': '0',
                            },
                            {
                                'uri': self.atypeV.uri,
                                'operator': '<',
                                'value': '10',
                            },
                        ],
                    },
                ]
            },
            {
                'id': self.otypeY.uri,
                'visible': False,
                'rules': [
                    {
                        'type': self.otypeE.uri,
                    },
                ]
            },
            {
                'id': self.otypeZ.uri,
                #'visible': True, ## this is the default
                'rules': [
                    {
                        'type': self.otypeD.uri,
                    },
                ]
            },
        ]
        self.src = self.base.create_stored_trace("s/", self.model_src, default_subject="alice")

    def test_missing_parameter(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.hrules,
                                         {"model": self.model_dst.uri,},
                                         [self.src],)
        with pytest.raises(CanNotProceedError):
            ctr.obsel_collection.force_state_refresh()
        assert ctr.diagnosis is not None

    def test_base_rules(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.hrules,
                                         {"rules": dumps(self.base_rules),
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        oE = self.src.create_obsel("oE", self.otypeE, 0)
        assert len(ctr.obsels) == 0 # no new obsel, rule is not visible
        oA = self.src.create_obsel("oA", self.otypeA, 1)
        assert len(ctr.obsels) == 1 # new obsel
        assert_obsel_type(ctr.obsels[-1], self.otypeX)
        assert_source_obsels(ctr.obsels[-1], [oA,])
        oB1 = self.src.create_obsel("oB1", self.otypeB, 2)
        assert len(ctr.obsels) == 1 # no new obsel, oB1 has no attribute atF
        oB2 = self.src.create_obsel("oB2", self.otypeB, 3,
                                    attributes={self.atypeV: Literal(42)})
        assert len(ctr.obsels) == 1 # no new obsel, oB2 has atV != 0
        oB3 = self.src.create_obsel("oB3", self.otypeB, 4,
                                    attributes={self.atypeV: Literal(0)})
        assert len(ctr.obsels) == 2 # new obsel
        assert_obsel_type(ctr.obsels[-1], self.otypeX)
        assert_source_obsels(ctr.obsels[-1], [oB3,])
        oD = self.src.create_obsel("oD", self.otypeD, 5)
        assert len(ctr.obsels) == 3 # new obsel
        assert_obsel_type(ctr.obsels[-1], self.otypeZ)
        assert_source_obsels(ctr.obsels[-1], [oD,])

        # TODO more tests

        # TODO test precedence of rules (once implemented)

        # TODO test misc datatypes of values (once implemented)
