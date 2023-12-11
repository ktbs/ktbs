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
import pytest
from rdflib import RDF, XSD

from ktbs.methods.parallel import LOG as PARALLEL_LOG
from ktbs.namespace import KTBS, KTBS_NS_URI
from rdfrest.exceptions import CanNotProceedError

from .test_ktbs_engine import KtbsTestCase

def assert_obsel_types(obsels, obsel_types):
    lst1 = [ o.state.value(o.uri, RDF.type) for o in obsels ]
    lst2 = [ ot.uri for ot in obsel_types ]
    assert lst1 == lst2

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

class TestParallel(KtbsTestCase):

    def setup_method(self):
        KtbsTestCase.setup_method(self)
        self.log = PARALLEL_LOG
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
        self.model_dst1 = self.base.create_model("md1")
        self.otypeX = self.model_dst1.create_obsel_type("#otX")
        self.otypeY = self.model_dst1.create_obsel_type("#otY")
        self.otypeZ = self.model_dst1.create_obsel_type("#otZ")
        self.model_dst2 = self.base.create_model("md2")
        self.otypeU = self.model_dst2.create_obsel_type("#otU")
        self.otypeV = self.model_dst2.create_obsel_type("#otV")
        self.model_dst3 = self.base.create_model("md3")
        self.model_dst3.add_parent(self.model_src)
        self.model_dst3.add_parent(self.model_dst1)
        self.model_dst3.add_parent(self.model_dst2)

        self.src = self.base.create_stored_trace("s/", self.model_src, default_subject="alice")

        self.m1 = self.base.create_method("m1", KTBS.sparql, {
            "model": str(self.model_dst1.uri),
            "inherit": "true",
            "sparql": """
                PREFIX : <%s#>
                PREFIX m: <%s#>
                PREFIX md: <%s#>

                CONSTRUCT {
                  [ :hasSourceObsel ?obs ; a ?newtyp;  ]
                } WHERE {
                  ?obs :hasTrace <%%(__source__)s> ; a ?typ.
                  values (?typ ?newtyp) { (m:otA md:otX) (m:otB md:otY) }
                }
            """ % (KTBS_NS_URI, self.model_src.uri, self.model_dst1.uri)
        })
        self.m2 = self.base.create_method("m2", KTBS.sparql, {
            "model": str(self.model_dst2.uri),
            "inherit": "true",
            "sparql": """
                PREFIX : <%s#>
                PREFIX m: <%s#>
                PREFIX md: <%s#>

                CONSTRUCT {
                  [ :hasSourceObsel ?obs ; a ?newtyp ; :hasBegin ?newb ]
                } WHERE {
                  ?obs :hasTrace <%%(__source__)s> ; a ?typ ; :hasBegin ?b.
                  BIND(?b-1 as ?newb)
                  values (?typ ?newtyp) { (m:otA md:otU) (m:otB md:otV) }
                }
            """ % (KTBS_NS_URI, self.model_src.uri, self.model_dst2.uri)
        })
        self.m3 = self.base.create_method("m3", KTBS.sparql, {
            "model": str(self.model_dst2.uri),
            "inherit": "true",
            "sparql": """
                PREFIX : <%s#>
                PREFIX m: <%s#>
                PREFIX md: <%s#>

                CONSTRUCT {
                  [ :hasSourceObsel ?obs ; a ?newtyp ; :hasBegin ?newb ]
                } WHERE {
                  ?obs :hasTrace <%%(__source__)s> ; a ?typ ; :hasBegin ?b.
                  BIND(?b-2 as ?newb)
                  values (?typ ?newtyp) { (m:otA md:otZ) (m:otB md:otZ) }
                }
            """ % (KTBS_NS_URI, self.model_src.uri, self.model_dst1.uri)
        })

    def test_missing_methods(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.parallel,
                                         {},
                                         [self.src],)
        with pytest.raises(CanNotProceedError):
            ctr.obsel_collection.force_state_refresh()
        assert ctr.diagnosis is not None

    def test_missing_model(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.parallel,
                                         { 'methods': ' '.join(
                                             [self.m1.uri, self.m2.uri]),
                                         },
                                         [self.src],)
        with pytest.raises(CanNotProceedError):
            ctr.obsel_collection.force_state_refresh()
        assert ctr.diagnosis is not None

    def test_simple_parallel(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.parallel,
                                         {
                                             "methods": ' '.join(
                                                [self.m1.uri, self.m2.uri]),
                                             "model": self.model_dst3.uri,
                                         },
                                         [self.src],)

        otX = self.otypeX
        otY = self.otypeY
        otU = self.otypeU
        otV = self.otypeV

        obs = self.src.create_obsel(None, self.otypeA, 10)
        assert len(ctr.obsels) == 2
        assert_obsel_types(ctr.obsels, [otU, otX])
        assert_rec_source_obsels(ctr.obsels[-1], [obs])
        assert_rec_source_obsels(ctr.obsels[-2], [obs])

        obs = self.src.create_obsel(None, self.otypeB, 11)
        assert len(ctr.obsels) == 4
        assert_obsel_types(ctr.obsels, [otU, otX, otV, otY])
        assert_rec_source_obsels(ctr.obsels[-1], [obs])
        assert_rec_source_obsels(ctr.obsels[-2], [obs])

    def test_changing_parallel(self):
        ctr = self.base.create_computed_trace("ctr/", KTBS.parallel,
                                         {
                                             "methods": ' '.join(
                                                [self.m1.uri, self.m2.uri]),
                                             "model": self.model_dst3.uri,
                                         },
                                         [self.src],)

        otX = self.otypeX
        otY = self.otypeY
        otZ = self.otypeZ
        otU = self.otypeU
        otV = self.otypeV

        self.src.create_obsel(None, self.otypeA, 10)
        self.src.create_obsel(None, self.otypeB, 11)
        assert_obsel_types(ctr.obsels, [otU, otX, otV, otY])
        assert self.base.get('_0_ctr/') is not None
        assert self.base.get('_1_ctr/') is not None
        assert self.base.get('_2_ctr/') is None


        ctr.set_parameter("methods", ' '.join([self.m1.uri, self.m3.uri]))
        assert_obsel_types(ctr.obsels, [otZ, otX, otZ, otY])
        assert self.base.get('_0_ctr/') is not None
        assert self.base.get('_1_ctr/') is not None
        assert self.base.get('_2_ctr/') is None

        ctr.set_parameter("methods", ' '.join([self.m2.uri, self.m1.uri]))
        assert_obsel_types(ctr.obsels, [otU, otX, otV, otY])
        assert self.base.get('_0_ctr/') is not None
        assert self.base.get('_1_ctr/') is not None
        assert self.base.get('_2_ctr/') is None

        ctr.set_parameter("methods", ' '.join([self.m2.uri, self.m1.uri, self.m3.uri]))
        assert_obsel_types(ctr.obsels, [otZ, otU, otX, otZ, otV, otY])
        assert self.base.get('_0_ctr/') is not None
        assert self.base.get('_1_ctr/') is not None
        assert self.base.get('_2_ctr/') is not None

        ctr.set_parameter("methods", ' '.join([self.m2.uri]))
        assert_obsel_types(ctr.obsels, [otU, otV])
        assert self.base.get('_0_ctr/') is not None
        assert self.base.get('_1_ctr/') is None
        assert self.base.get('_2_ctr/') is None
