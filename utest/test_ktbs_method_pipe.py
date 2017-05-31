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
from rdflib import XSD

from ktbs.methods.pipe import LOG as PIPE_LOG
from ktbs.namespace import KTBS, KTBS_NS_URI
from rdfrest.exceptions import CanNotProceedError

from .test_ktbs_engine import KtbsTestCase

def assert_obsel_type(obsel, obsel_type):
    assert obsel.obsel_type.uri == obsel_type.uri

def assert_rec_source_obsels(obsel, source_obsels):
    assert set(iter_rec_source_obsels(obsel)) == set(source_obsels)

def iter_rec_source_obsels(obsel):
    sobsels = obsel.source_obsels
    if not sobsels:
        yield obsel
    else:
        for sobs in sobsels:
            for ssobs in iter_rec_source_obsels(sobs):
                yield ssobs

import logging
logging.basicConfig()


class TestPipe(KtbsTestCase):

    def setup(self):
        KtbsTestCase.setup(self)
        self.log = PIPE_LOG
        self.base = self.my_ktbs.create_base("b/")
        self.model_src = self.base.create_model("ms")
        self.otypeA = self.model_src.create_obsel_type("#otA")
        self.otypeB = self.model_src.create_obsel_type("#otB")
        all_types = [self.otypeA, self.otypeB]
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

        self.m1 = self.base.create_method("m1", KTBS.sparql, {
            "inherit": "true",
            "sparql": """
                PREFIX : <%s#>
                PREFIX m: <%s#>
                
                CONSTRUCT {
                  [ :hasSourceObsel ?obs ; m:V 42 ]
                } WHERE {
                  ?obs :hasTrace <%%(__source__)s>
                }
            """ % (KTBS_NS_URI, self.model_src.uri)
        })
        self.m2 = self.base.create_method("m2", KTBS.sparql, {
            "model": str(self.model_dst.uri),
            "inherit": "true",
            "sparql": """
                PREFIX : <%s#>
                PREFIX m: <%s#>
                PREFIX md: <%s#>

                CONSTRUCT {
                  [ :hasSourceObsel ?obs ; a ?newtyp ]
                } WHERE {
                  ?obs :hasTrace <%%(__source__)s> ; a ?typ. 
                  values (?typ ?newtyp) { (m:otA md:otX) (m:otB md:otY) }
                }
            """ % (KTBS_NS_URI, self.model_src.uri, self.model_dst.uri)
        })
        self.m3 = self.base.create_method("m3", KTBS.sparql, {
            "model": str(self.model_dst.uri),
            "inherit": "true",
            "sparql": """
                PREFIX : <%s#>
                PREFIX m: <%s#>
                PREFIX md: <%s#>

                CONSTRUCT {
                  [ :hasSourceObsel ?obs ; a ?newtyp ]
                } WHERE {
                  ?obs :hasTrace <%%(__source__)s> ; a ?typ. 
                  values (?typ ?newtyp) {
                    (m:otA md:otY) (m:otB md:otX)
                    (md:otX md:otY) (md:otY md:otX)
                  }
                }
            """ % (KTBS_NS_URI, self.model_src.uri, self.model_dst.uri)
        })

    def test_missing_parameter(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.pipe,
                                         {},
                                         [self.src],)
        with pytest.raises(CanNotProceedError):
            ctr.obsel_collection.force_state_refresh()
        assert ctr.diagnosis is not None

    def test_simple_pipe(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.pipe,
                                         {"methods": ' '.join(
                                             [self.m1.uri, self.m2.uri]),
                                         },
                                         [self.src],)
        obs = self.src.create_obsel(None, self.otypeA, 0)
        assert len(ctr.obsels) == 1
        assert_obsel_type(ctr.obsels[-1], self.otypeX)
        assert_rec_source_obsels(ctr.obsels[-1], [obs])
        assert ctr.obsels[-1].begin == 0

        obs = self.src.create_obsel(None, self.otypeA, 1)
        assert len(ctr.obsels) == 2
        assert_obsel_type(ctr.obsels[-1], self.otypeX)
        assert_rec_source_obsels(ctr.obsels[-1], [obs])
        assert ctr.obsels[-1].begin == 1

        obs = self.src.create_obsel(None, self.otypeA, 3)
        assert_obsel_type(ctr.obsels[-1], self.otypeX)
        assert_rec_source_obsels(ctr.obsels[-1], [obs])
        assert ctr.obsels[-1].begin == 3

        obs = self.src.create_obsel(None, self.otypeB, 2)
        assert len(ctr.obsels) == 4
        assert_obsel_type(ctr.obsels[-2], self.otypeY)
        assert_rec_source_obsels(ctr.obsels[-2], [obs])
        assert ctr.obsels[-2].begin == 2

    def test_changing_pipe(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.pipe,
                                         {"methods": ' '.join(
                                             [self.m1.uri, self.m2.uri]),
                                         },
                                         [self.src],)
        obs = self.src.create_obsel(None, self.otypeA, 0)
        obs = self.src.create_obsel(None, self.otypeA, 1)
        obs = self.src.create_obsel(None, self.otypeA, 3)
        obs = self.src.create_obsel(None, self.otypeB, 2)

        otA = self.otypeA.uri
        otB = self.otypeB.uri
        otX = self.otypeX.uri
        otY = self.otypeY.uri
        assert [ o.obsel_type.uri for o in ctr.obsels] == [otX, otX, otY, otX]

        ctr.set_parameter("methods", ' '.join([self.m1.uri, self.m3.uri]))
        assert [ o.obsel_type.uri for o in ctr.obsels] == [otY, otY, otX, otY]
        assert self.base.get('_0_ctr/') is not None
        assert self.base.get('_1_ctr/') is not None
        assert self.base.get('_2_ctr/') is None

        ctr.set_parameter("methods", ' '.join([self.m1.uri, self.m2.uri, self.m3.uri]))
        assert [ o.obsel_type.uri for o in ctr.obsels] == [otY, otY, otX, otY]
        assert self.base.get('_0_ctr/') is not None
        assert self.base.get('_1_ctr/') is not None
        assert self.base.get('_2_ctr/') is not None

        ctr.set_parameter("methods", ' '.join([self.m1.uri]))
        assert [ o.obsel_type.uri for o in ctr.obsels] == [otA, otA, otB, otA]
        assert self.base.get('_0_ctr/') is not None
        assert self.base.get('_1_ctr/') is None
        assert self.base.get('_2_ctr/') is None
