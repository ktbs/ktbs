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

from fsa4streams.fsa import FSA
from json import dumps, loads
from rdflib import Literal, XSD

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
    assert obsel.obsel_type.uri == obsel_type.uri

def assert_source_obsels(obsel, source_obsels):
    assert set(obsel.iter_source_obsels()) == set(source_obsels)




class TestFSA(KtbsTestCase):

    def setup(self):
        KtbsTestCase.setup(self)
        self.log = FSA_LOG
        self.base = self.my_ktbs.create_base("b/")
        self.model_src = self.base.create_model("ms")
        self.A= self.model_src.create_obsel_type("#A")
        self.B= self.model_src.create_obsel_type("#B")
        self.foo = self.model_src.create_attribute_type("#foo")
        self.bar = self.model_src.create_attribute_type("#bar")
        self.model_dst = self.base.create_model("md")
        self.X = self.model_dst.create_obsel_type("#X")
        self.Y = self.model_dst.create_obsel_type("#Y")
        self.fubar = self.model_dst.create_attribute_type("#fubar")
        self.src = self.base.create_stored_trace("s/", self.model_src, default_subject="alice")

    def test_simple_with_union(self):
        sparql = """
        PREFIX ms: <%(base)s/ms#>
        PREFIX md: <%(base)s/md#>

        SELECT ?sourceObsel ?type (?sourceBegin as ?begin) (?sourceEnd as ?end) ?fubar
        {
            %%(__subselect__)s

            {
              ?sourceObsel a ms:A .
              BIND(md:X as ?type)
              BIND(1 as ?mult)
            }
            UNION
            {
              ?sourceObsel a ms:B .
              BIND(md:Y as ?type)
              BIND(-1 as ?mult)
            }

            ?sourceObsel ms:foo ?foo.
            OPTIONAL {?sourceObsel ms:bar ?bar }
            BIND(?foo+?bar*?mult as ?fubar)

        }
        """ % { 'base': self.base.uri[:-1], }
        ctr = self.base.create_computed_trace("ctr/", KTBS.isparql,
                                         {"sparql": sparql,
                                          "model": self.model_dst.uri,},
                                         [self.src],)
        assert len(ctr.obsels) == 0

        oA0 = self.src.create_obsel("oA0", self.A, 0, attributes={self.foo: 42})
        orig_obs = oA0
        assert len(ctr.obsels) == 1
        new_obs = ctr.obsels[-1]
        assert_source_obsels(new_obs, [orig_obs])
        assert new_obs.begin == orig_obs.begin
        assert new_obs.end == orig_obs.end
        assert get_custom_state(ctr, 'last_seen_u') == unicode(orig_obs.uri)
        assert get_custom_state(ctr, 'last_seen_b') == orig_obs.begin
        assert_obsel_type(new_obs, self.X)
        assert new_obs.get_attribute_value(self.fubar) is None

        oA1 = self.src.create_obsel("oA1", self.A, 1, attributes={
            self.foo: 101, self.bar: 42})
        orig_obs = oA1
        assert len(ctr.obsels) == 2
        new_obs = ctr.obsels[-1]
        assert_source_obsels(new_obs, [orig_obs])
        assert new_obs.begin == orig_obs.begin
        assert new_obs.end == orig_obs.end
        assert get_custom_state(ctr, 'last_seen_u') == unicode(orig_obs.uri)
        assert get_custom_state(ctr, 'last_seen_b') == orig_obs.begin
        assert_obsel_type(new_obs, self.X)
        assert new_obs.get_attribute_value(self.fubar) == 101+42

        oB2 = self.src.create_obsel("oB2", self.B, 2, 4, attributes={
            self.foo: 101, self.bar: 42})
        orig_obs = oB2
        assert len(ctr.obsels) == 3
        new_obs = ctr.obsels[-1]
        assert_source_obsels(new_obs, [orig_obs])
        assert new_obs.begin == orig_obs.begin
        assert new_obs.end == orig_obs.end
        assert get_custom_state(ctr, 'last_seen_u') == unicode(orig_obs.uri)
        assert get_custom_state(ctr, 'last_seen_b') == orig_obs.begin
        assert_obsel_type(new_obs, self.Y)
        assert new_obs.get_attribute_value(self.fubar) == 101-42
