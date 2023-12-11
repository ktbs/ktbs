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

    def setup_method(self):
        KtbsTestCase.setup_method(self)
        self.log = HRULES_LOG
        self.base = self.my_ktbs.create_base("b/")
        self.model_src = self.base.create_model("ms")
        self.otypeA = self.model_src.create_obsel_type("#otA")
        self.otypeB = self.model_src.create_obsel_type("#otB")
        self.otypeC = self.model_src.create_obsel_type("#otC")
        self.otypeD = self.model_src.create_obsel_type("#otD")
        self.otypeE = self.model_src.create_obsel_type("#otE")
        all_types = [self.otypeA, self.otypeB, self.otypeC, self.otypeD,
                     self.otypeE]
        self.atypeT = self.model_src.create_attribute_type("#atT")
        self.atypeU = self.model_src.create_attribute_type("#atU", all_types,
                                                           [XSD.integer])
        self.atypeV = self.model_src.create_attribute_type("#atV", all_types,
                                                           [XSD.decimal])
        self.atypeW = self.model_src.create_attribute_type("#atW", all_types,
                                                           [XSD.string])
        self.model_dst = self.base.create_model("md")
        self.otypeX = self.model_dst.create_obsel_type("#otX")
        self.otypeY = self.model_dst.create_obsel_type("#otY")
        self.otypeZ = self.model_dst.create_obsel_type("#otZ")
        self.src = self.base.create_stored_trace("s/", self.model_src, default_subject="alice")

    def test_missing_parameter(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.hrules,
                                         {"model": self.model_dst.uri,},
                                         [self.src],)
        with pytest.raises(CanNotProceedError):
            ctr.obsel_collection.force_state_refresh()
        assert ctr.diagnosis is not None

    def test_base_rules(self):
        base_rules = [
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
        ctr = self.base.create_computed_trace("ctr/", KTBS.hrules,
                                         {"rules": dumps(base_rules),
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

    def test_precedence(self):
        base_rules = [
            {
                'id': self.otypeX.uri,
                'rules': [
                    {
                        'type': self.otypeE.uri,
                    },
                ]
            },
            {
                'id': self.otypeY.uri,
                'rules': [
                    {
                        'type': self.otypeA.uri,
                    },
                    {
                        'type': self.otypeE.uri,
                        'attributes': [
                            {
                                'uri': self.atypeU.uri,
                                'operator': '<',
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
                'id': self.otypeZ.uri,
                'rules': [
                    {
                        'type': self.otypeB.uri,
                    },
                    {
                        'type': self.otypeE.uri,
                        'attributes': [
                            {
                                'uri': self.atypeU.uri,
                                'operator': '>=',
                                'value': '0',
                            },
                        ],
                    },
                    {
                        'attributes': [
                            {
                                'uri': self.atypeV.uri,
                                'operator': '>=',
                                'value': '6',
                            },
                            {
                                'uri': self.atypeV.uri,
                                'operator': '>=',
                                'value': '8',
                            },
                        ],
                    },
                ]
            },
        ]
        ctr = self.base.create_computed_trace("ctr/", KTBS.hrules,
                                              {"rules": dumps(base_rules),
                                               "model": self.model_dst.uri, },
                                              [self.src], )

        nobs = 0
        for old_type, attr_u, attr_v, new_type in [
            (self.otypeA, None, None, self.otypeY),
            (self.otypeB, None, None, self.otypeZ),
            (self.otypeE, None, None, self.otypeX),
            (self.otypeE, -1,   None, self.otypeY),
            (self.otypeE, 1,    None, self.otypeZ),
            (self.otypeE, None, 7,    self.otypeX),
            (self.otypeE, -1  , 7,    self.otypeY),
            (self.otypeE, 1   , 7,    self.otypeZ),
            (self.otypeA, None, 7,    self.otypeY),
            (self.otypeB, None, 7,    self.otypeZ),
            (self.otypeA, None, 11,   self.otypeY),
            (self.otypeB, None, 11,   self.otypeZ),
            (self.otypeC, None, 7,    self.otypeY),
        ]:
            nobs += 1
            attr = {}
            if attr_u is not None:
                attr[self.atypeU] = Literal(attr_u)
            if attr_v is not None:
                attr[self.atypeV] = Literal(attr_v)
            obs = self.src.create_obsel(None, old_type, nobs, attributes=attr)
            assert len(ctr.obsels) == nobs
            assert_obsel_type(ctr.obsels[-1], new_type)
            assert_source_obsels(ctr.obsels[-1], [obs,])

        obs = self.src.create_obsel(None, self.otypeC, nobs+1)
        assert len(ctr.obsels) == nobs # no new obsel created

    def test_datatypes(self):
        base_rules = [
            {
                'id': self.otypeX.uri,
                'rules': [
                    {
                        'attributes': [
                            {
                                'uri': self.atypeU.uri,
                                'operator': '<',
                                'value': '50',
                            },
                        ],
                    },
                    {
                        'attributes': [
                            {
                                'uri': self.atypeV.uri,
                                'operator': '<',
                                'value': '50',
                            },
                        ],
                    },
                ]
            },
            {
                'id': self.otypeY.uri,
                'rules': [
                    {
                        'attributes': [
                            {
                                'uri': self.atypeT.uri,
                                'operator': '<',
                                'value': '50',
                            },
                        ],
                    },
                    {
                        'attributes': [
                            {
                                'uri': self.atypeW.uri,
                                'operator': '<',
                                'value': '50',
                            },
                        ],
                    },
                ]
            },
            {
                'id': self.otypeZ.uri,
                'rules': [
                    {
                        'type': self.otypeE.uri,
                        'attributes': [
                            {
                                'uri': self.atypeT.uri,
                                'operator': '>',
                                'value': {
                                    '@value': "999",
                                    '@datatype': XSD.int,
                                },
                            },
                        ],
                    },
                ]
            },
        ]
        ctr = self.base.create_computed_trace("ctr/", KTBS.hrules,
                                              {"rules": dumps(base_rules),
                                               "model": self.model_dst.uri, },
                                              [self.src], )

        obs = self.src.create_obsel(None, self.otypeA, 1,
                                    attributes={self.atypeU: Literal(6)})
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[-1], self.otypeX)
        assert_source_obsels(ctr.obsels[-1], [obs,])

        obs = self.src.create_obsel(None, self.otypeA, 2,
                                    attributes={self.atypeV: Literal(6.5)})
        assert len(ctr.obsels) == 2
        assert_obsel_type(ctr.obsels[-1], self.otypeX)
        assert_source_obsels(ctr.obsels[-1], [obs,])

        obs = self.src.create_obsel(None, self.otypeA, 3,
                                    attributes={self.atypeT: Literal("400")})
        assert len(ctr.obsels) == 3
        assert_obsel_type(ctr.obsels[-1], self.otypeY)
        assert_source_obsels(ctr.obsels[-1], [obs, ])

        obs = self.src.create_obsel(None, self.otypeA, 4,
                                    attributes={self.atypeW: Literal("400")})
        assert len(ctr.obsels) == 4
        assert_obsel_type(ctr.obsels[-1], self.otypeY)
        assert_source_obsels(ctr.obsels[-1], [obs, ])


        obs = self.src.create_obsel(None, self.otypeE, 5,
                                    attributes={self.atypeT: Literal(1000)})
        assert len(ctr.obsels) == 5
        assert_obsel_type(ctr.obsels[-1], self.otypeZ)
        assert_source_obsels(ctr.obsels[-1], [obs, ])


        obs = self.src.create_obsel(None, self.otypeA, 6,
                                    attributes={self.atypeT: Literal("6")})
        assert len(ctr.obsels) == 5 # no new obsel created
        obs = self.src.create_obsel(None, self.otypeA, 7,
                                    attributes={self.atypeW: Literal("6")})
        assert len(ctr.obsels) == 5 # no new obsel created
        obs = self.src.create_obsel(None, self.otypeA, 8,
                                    attributes={self.atypeU: Literal(400)})
        assert len(ctr.obsels) == 5 # no new obsel created
        obs = self.src.create_obsel(None, self.otypeA, 9,
                                    attributes={self.atypeU: Literal(400)})
        assert len(ctr.obsels) == 5 # no new obsel created

    def test_numeric_operators(self):
        base_rules = [
            {
                'id': self.otypeX.uri,
                'rules': [
                    {
                        'type': self.otypeA.uri,
                        'attributes': [
                            {
                                'uri': self.atypeV.uri,
                                'operator': '==',
                                'value': '10',
                            },
                        ],
                    },
                ]
            },
        ]

        for i in range(5):
            self.src.create_obsel(f"o{i}", self.otypeA, i*5,
                                  attributes={self.atypeV: Literal(i*5)})

        for (i, op) in enumerate(['==', '!=', '<', '>', '>=', '<=',]):
            base_rules[0]['rules'][0]['attributes'][0]['operator'] = op
            ctr = self.base.create_computed_trace(f"ctr{i}/", KTBS.hrules,
                                                  {"rules": dumps(base_rules),
                                                   "model": self.model_dst.uri,},
                                                  [self.src],)
            got = [obs.begin for obs in ctr.obsels]
            exp = {
                '==': [10,],
                '!=': [0, 5, 15, 20,],
                '<': [0, 5,],
                '>': [15, 20,],
                '<=': [0, 5, 10,],
                '>=': [10, 15, 20,],
            }[op]
            assert got == exp

    def test_string_operators(self):
        base_rules = [
            {
                'id': self.otypeX.uri,
                'rules': [
                    {
                        'type': self.otypeA.uri,
                        'attributes': [
                            {
                                'uri': self.atypeW.uri,
                                'operator': '==',
                                'value': '2',
                            },
                        ],
                    },
                ]
            },
        ]

        for i in range(0, 6):
            isq = i**2
            self.src.create_obsel(f"o{i}", self.otypeA, isq,
                                  attributes={self.atypeW: Literal(str(isq))})

        for (i, op) in enumerate(['==', '!=', '<', '>', '>=', '<=', 'contains']):
            base_rules[0]['rules'][0]['attributes'][0]['operator'] = op
            ctr = self.base.create_computed_trace(f"ctr{i}/", KTBS.hrules,
                                                  {"rules": dumps(base_rules),
                                                   "model": self.model_dst.uri,},
                                                  [self.src],)
            got = [obs.begin for obs in ctr.obsels]
            exp = {
                '==': [],
                '!=': [0, 1, 4, 9, 16, 25],
                '<': [0, 1, 16],
                '>': [4, 9, 25],
                '<=': [0, 1, 16],
                '>=': [4, 9, 25],
                'contains': [25,]
            }[op]
            assert got == exp, f"for {op}"
