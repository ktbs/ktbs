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
from pytest import raises as assert_raises

from json import loads

from ktbs.engine.resource import METADATA
from ktbs.methods.fusion import LOG as FUSION_LOG
from ktbs.methods.filter import LOG as FILTER_LOG
from ktbs.namespace import KTBS, KTBS_NS_URI
from rdfrest.exceptions import CanNotProceedError

from .test_ktbs_engine import KtbsTestCase, HttpKtbsTestCaseMixin

def get_custom_state(computed_trace, key=None):
        jsonstr = computed_trace.metadata.value(computed_trace.uri,
                                                METADATA.computation_state)
        jsonobj = loads(jsonstr)
        ret = jsonobj.get('custom')
        if ret is not None and key is not None:
            ret = ret.get(key)
        return ret


class TestFilter(KtbsTestCase):

    log = FILTER_LOG

    def test_filter_temporal(self):
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype = model.create_obsel_type("#ot")
        src = base.create_stored_trace("s/", model, default_subject="alice")
        ctr = base.create_computed_trace("ctr/", KTBS.filter,
                                         {"after": "10", "before": "20"},
                                         [src],)
        assert get_custom_state(ctr, 'last_seen_u') == None
        assert get_custom_state(ctr, 'passed_maxtime') == False

        self.log.info(">first change (considered non-monotonic): add o00")
        o00 = src.create_obsel("o00", otype, 0)
        assert len(ctr.obsels) == 0
        assert get_custom_state(ctr, 'last_seen_u') == None # not even looked at
        assert get_custom_state(ctr, 'passed_maxtime') == False

        self.log.info(">strictly temporally monotonic change: add o05")
        o05 = src.create_obsel("o05", otype, 5)
        assert len(ctr.obsels) == 0
        assert get_custom_state(ctr, 'last_seen_u') == None # not event looked at
        assert get_custom_state(ctr, 'passed_maxtime') == False

        self.log.info(">strictly temporally monotonic change: add o10")
        o10 = src.create_obsel("o10", otype, 10)
        assert len(ctr.obsels) == 1
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o10.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 10
        assert get_custom_state(ctr, 'passed_maxtime') == False

        self.log.info(">strictly temporally monotonic change: add o15")
        o15 = src.create_obsel("o15", otype, 15)
        assert len(ctr.obsels) == 2
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o15.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 15
        assert get_custom_state(ctr, 'passed_maxtime') == False

        self.log.info(">strictly temporally monotonic change: add o20")
        o20 = src.create_obsel("o20", otype, 20)
        assert len(ctr.obsels) == 3
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o20.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 20
        assert get_custom_state(ctr, 'passed_maxtime') == False

        self.log.info(">strictly temporally monotonic change: add o25")
        o25 = src.create_obsel("o25", otype, 25)
        assert len(ctr.obsels) == 3
        assert get_custom_state(ctr, 'passed_maxtime') == True

        self.log.info(">strictly temporally monotonic change: add o30")
        o30 = src.create_obsel("o30", otype, 30)
        assert len(ctr.obsels) == 3
        assert get_custom_state(ctr, 'passed_maxtime') == True


        self.log.info(">non-temporally monotonic change: add o27")
        o27 = src.create_obsel("o27", otype, 27)
        assert len(ctr.obsels) == 3

        self.log.info(">non-temporally monotonic change: add o17")
        o17 = src.create_obsel("o17", otype, 17)
        assert len(ctr.obsels) == 4

        self.log.info(">non-temporally monotonic change: add o07")
        o07 = src.create_obsel("o07", otype, 7)
        assert len(ctr.obsels) == 4


        self.log.info(">strictly temporally monotonic change: add o35")
        o35 = src.create_obsel("o35", otype, 35)
        assert len(ctr.obsels) == 4
        assert get_custom_state(ctr, 'passed_maxtime') == True


        self.log.info(">non-monotonic change: removing o15")
        with src.obsel_collection.edit() as editable:
            editable.remove((o15.uri, None, None))
            editable.remove((None, None, o15.uri))
        assert len(ctr.obsels) == 3
        assert get_custom_state(ctr, 'passed_maxtime') == True

        self.log.info(">non-monotonic change: removing o25")
        with src.obsel_collection.edit() as editable:
            editable.remove((o25.uri, None, None))
            editable.remove((None, None, o25.uri))
        assert len(ctr.obsels) == 3
        assert get_custom_state(ctr, 'passed_maxtime') == True


    def test_filter_temporal_intervals(self):
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype = model.create_obsel_type("#ot")
        src = base.create_stored_trace("s/", model, default_subject="alice")
        ctr = base.create_computed_trace("ctr/", KTBS.filter,
                                         {"after": "10", "before": "20"},
                                         [src],)

        self.log.info(">first change (considered non-monotonic): add o00")
        o8_15 = src.create_obsel("o8_15", otype, 8, 15)
        assert len(ctr.obsels) == 0
        o9_15 = src.create_obsel("o9_15", otype, 9, 15)
        assert len(ctr.obsels) == 0
        o10_15 = src.create_obsel("o10_15", otype, 10, 15)
        assert len(ctr.obsels) == 1
        o11_15 = src.create_obsel("o11_15", otype, 11, 15)
        assert len(ctr.obsels) == 2
        o13_15 = src.create_obsel("o13_15", otype, 13, 15)
        assert len(ctr.obsels) == 3
        o13_15a = src.create_obsel("o13_15a", otype, 13, 15)
        assert len(ctr.obsels) == 4
        o15_15 = src.create_obsel("o15_15", otype, 15, 15)
        assert len(ctr.obsels) == 5
        o15_17 = src.create_obsel("o15_17", otype, 15, 17)
        assert len(ctr.obsels) == 6
        o15_20 = src.create_obsel("o15_20", otype, 15, 20)
        assert len(ctr.obsels) == 7
        o15_21 = src.create_obsel("o15_21", otype, 15, 21)
        assert len(ctr.obsels) == 7
        assert get_custom_state(ctr, 'passed_maxtime') == True
        o15_19 = src.create_obsel("o15_19", otype, 15, 19)
        assert len(ctr.obsels) == 8
        assert get_custom_state(ctr, 'passed_maxtime') == True
        with src.obsel_collection.edit() as editable:
            editable.remove((o15_21.uri, None, None))
            editable.remove((None, None, o15_21.uri))
        assert len(ctr.obsels) == 8
        assert get_custom_state(ctr, 'passed_maxtime') == False


    def test_filter_otypes(self):
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype1 = model.create_obsel_type("#ot1")
        otype2 = model.create_obsel_type("#ot2")
        otype3 = model.create_obsel_type("#ot3")
        src = base.create_stored_trace("s/", model, default_subject="alice")
        ctr = base.create_computed_trace("ctr/", KTBS.filter,
                                         {"otypes": "%s %s" % (
                                              otype1.uri, otype2.uri,
                                          )},
                                         [src],)

        self.log.info(">strictly temporally monotonic change: add o00")
        o00 = src.create_obsel("o00", otype1, 0)
        assert len(ctr.obsels) == 1
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o00.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 0
        self.log.info(">strictly temporally monotonic change: add o05")
        o05 = src.create_obsel("o05", otype2, 5)
        assert len(ctr.obsels) == 2
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o05.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 5
        self.log.info(">strictly temporally monotonic change: add o10")
        o10 = src.create_obsel("o10", otype3, 10)
        assert len(ctr.obsels) == 2
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o10.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 10
        self.log.info(">strictly temporally monotonic change: add o15")
        o15 = src.create_obsel("o15", otype1, 15)
        assert len(ctr.obsels) == 3
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o15.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 15
        self.log.info(">strictly temporally monotonic change: add o20")
        o20 = src.create_obsel("o20", otype2, 20)
        assert len(ctr.obsels) == 4
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o20.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 20
        self.log.info(">strictly temporally monotonic change: add o25")
        o25 = src.create_obsel("o25", otype3, 25)
        assert len(ctr.obsels) == 4
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o25.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 25
        self.log.info(">strictly temporally monotonic change: add o30")
        o30 = src.create_obsel("o30", otype1, 30)
        assert len(ctr.obsels) == 5
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30

        self.log.info(">non-temporally monotonic change: add o27")
        o27 = src.create_obsel("o27", otype2, 27)
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30
        assert len(ctr.obsels) == 6
        self.log.info(">non-temporally monotonic change: add o17")
        o17 = src.create_obsel("o17", otype1, 17)
        assert len(ctr.obsels) == 7
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30
        self.log.info(">non-temporally monotonic change: add o07")
        o07 = src.create_obsel("o07", otype2, 7)
        assert len(ctr.obsels) == 8
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30

        self.log.info(">strictly temporally monotonic change: add o35")
        o35 = src.create_obsel("o35", otype1, 35)
        assert len(ctr.obsels) == 9
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o35.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 35

        self.log.info(">non-monotonic change: removing o15")
        with src.obsel_collection.edit() as editable:
            editable.remove((o15.uri, None, None))
        assert len(ctr.obsels) == 8
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o35.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 35
        self.log.info(">non-monotonic change: removing o25")
        with src.obsel_collection.edit() as editable:
            editable.remove((o25.uri, None, None))
        assert len(ctr.obsels) == 8
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o35.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 35
        self.log.info(">non-monotonic change: removing o35")
        with src.obsel_collection.edit() as editable:
            editable.remove((o35.uri, None, None))
        assert len(ctr.obsels) == 7
        assert get_custom_state(ctr, 'last_seen_u') == unicode(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30


    def test_filter_relations(self):
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype = model.create_obsel_type("#ot")
        rtype = model.create_relation_type("#rt")
        src = base.create_stored_trace("s/", model, default_subject="alice")
        ctr = base.create_computed_trace("ctr/", KTBS.filter,
                                         {"after": "10", "before": "20"},
                                         [src],)

        o00 = src.create_obsel("o00", otype, 0)
        o05 = src.create_obsel("o05", otype, 5)
        o25 = src.create_obsel("o25", otype, 25)
        o30 = src.create_obsel("o30", otype, 30)
        assert len(ctr.obsels) == 0

        count_relations = lambda: \
            len(list(ctr.obsel_collection.state.triples((None, rtype.uri, None))))

        o10 = src.create_obsel("o10", otype, 10, relations=[(rtype, o00)])
        assert len(ctr.obsels) == 1
        assert count_relations() == 0
        o11 = src.create_obsel("o11", otype, 11, inverse_relations=[(o05, rtype)])
        assert len(ctr.obsels) == 2
        assert count_relations() == 0
        o12 = src.create_obsel("o12", otype, 12, relations=[(rtype, o25)])
        assert len(ctr.obsels) == 3
        assert count_relations() == 0
        o13 = src.create_obsel("o13", otype, 13, inverse_relations=[(o30, rtype)])
        assert len(ctr.obsels) == 4
        assert count_relations() == 0
        o14 = src.create_obsel("o14", otype, 14, relations=[(rtype, o12)])
        assert len(ctr.obsels) == 5
        assert count_relations() == 1
        o15 = src.create_obsel("o15", otype, 15, inverse_relations=[(o13, rtype)])
        assert len(ctr.obsels) == 6
        assert count_relations() == 2


class TestFusion(KtbsTestCase):

    def test_fusion(self):
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype = model.create_obsel_type("#ot")
        origin = "orig-abc"
        src1 = base.create_stored_trace("s1/", model, origin=origin,
                                        default_subject="alice")
        src2 = base.create_stored_trace("s2/", model, origin=origin,
                                        default_subject="bob")
        ctr = base.create_computed_trace("ctr/", KTBS.fusion, {},
                                         [src1, src2],)

        assert ctr.model == model
        assert ctr.origin == origin
        assert len(ctr.obsels) == 0

        o10 = src1.create_obsel("o10", otype, 0)
        assert len(ctr.obsels) == 1
        o21 = src2.create_obsel("o21", otype, 10)
        assert len(ctr.obsels) == 2
        o12 = src1.create_obsel("o12", otype, 20)
        assert len(ctr.obsels) == 3
        o23 = src2.create_obsel("o23", otype, 30)
        assert len(ctr.obsels) == 4
        o11 = src1.create_obsel("o11", otype, 10)
        assert len(ctr.obsels) == 5
        o20 = src2.create_obsel("o20", otype, 0)
        assert len(ctr.obsels) == 6

        with src1.obsel_collection.edit() as editable:
            editable.remove((o10.uri, None, None))
        assert len(ctr.obsels) == 5

        with src2.obsel_collection.edit() as editable:
            editable.remove((o21.uri, None, None))
        assert len(ctr.obsels) == 4


class TestExternal(KtbsTestCase):

    def test_external_no_source(self):
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype = model.create_obsel_type("#ot")
        origin = "orig-abc"
        cmdline = """cat <<EOF
        @prefix : <http://liris.cnrs.fr/silex/2009/ktbs> .
        @prefix m: <http://example.org/model#> .

        [] a m:Event ; :hasTrace <> ;
          :hasBegin 0 ; :hasEnd 0; :hasSubject "Alice" .\nEOF
        """
        ctr = base.create_computed_trace("ctr/", KTBS.external, {
                                             "command-line": cmdline,
                                             "model": model.uri,
                                             "origin": origin,
                                         }, [],)

        assert ctr.model == model
        assert ctr.origin == origin
        assert len(ctr.obsels) == 0


    def test_external_one_source(self):
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype = model.create_obsel_type("#ot")
        atype = model.create_attribute_type("#at")
        origin = "orig-abc"
        src1 = base.create_stored_trace("s1/", model, origin=origin,
                                        default_subject="alice")
        cmdline = """sed 's|%(__sources__)s||'"""
        ctr = base.create_computed_trace("ctr/", KTBS.external, {
                                             "command-line": cmdline,
                                             "feed-to-stdin": True,
                                             "foo": "bar"
                                         }, [src1],)

        assert ctr.model == model
        assert ctr.origin == origin
        assert len(ctr.obsels) == 0

        o10 = src1.create_obsel("o10", otype, 0)
        assert len(ctr.obsels) == 1
        o21 = src1.create_obsel("o21", otype, 10)
        assert len(ctr.obsels) == 2
        o12 = src1.create_obsel("o12", otype, 20)
        assert len(ctr.obsels) == 3
        o23 = src1.create_obsel("o23", otype, 30)
        assert len(ctr.obsels) == 4
        o11 = src1.create_obsel("o11", otype, 10)
        assert len(ctr.obsels) == 5
        o20 = src1.create_obsel("o20", otype, 0)
        assert len(ctr.obsels) == 6

        with src1.obsel_collection.edit() as editable:
            editable.remove((o10.uri, None, None))
        assert len(ctr.obsels) == 5

        with src1.obsel_collection.edit() as editable:
            editable.remove((o21.uri, None, None))
        assert len(ctr.obsels) == 4


class TestSparql(KtbsTestCase):

    def setup(self):
        super(TestSparql, self).setup()
        self.base = self.my_ktbs.create_base("b/")
        self.model = self.base.create_model("m")
        self.otype1 = self.model.create_obsel_type("#ot1")
        self.otype2 = self.model.create_obsel_type("#ot2")
        self.atype = self.model.create_attribute_type("#at")
        self.origin = "orig-abc"
        self.src1 = self.base.create_stored_trace("s1/", self.model,
                                                  origin=self.origin,
                                                  default_subject="alice")

    def test_sparql_one_source(self):
        sparql = """
        PREFIX : <http://example.org/model#>
        PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>

        CONSTRUCT {
            [ k:hasTrace <%(__destination__)s> ;
              a ?ot ;
              k:hasBegin ?begin ;
              k:hasEnd   ?begin ;
              k:hasSubject "anonymous" ;
              k:hasSourceObsel ?sobs ;
              :at "%(foo)s"
            ]
        }
        WHERE {
            ?sobs a ?ot ; k:hasBegin ?begin .
        }
        """
        ctr = self.base.create_computed_trace("ctr/", KTBS.sparql, {
                                                  "sparql": sparql,
                                                  "foo": "bar"
                                              }, [self.src1],)
        assert not ctr.diagnosis
        assert ctr.model == self.model
        assert ctr.origin == self.origin
        assert len(ctr.obsels) == 0

        o10 = self.src1.create_obsel("o10", self.otype1, 0,
                                     attributes = {self.atype: "héhé"})
        # above, we force some non-ascii output of the script,
        # to check that UTF-8 is corectly decoded by the method
        ctr.obsel_collection.force_state_refresh()
        assert ctr.diagnosis == None

        assert len(ctr.obsels) == 1
        o21 = self.src1.create_obsel("o21", self.otype1, 10)
        assert len(ctr.obsels) == 2
        o12 = self.src1.create_obsel("o12", self.otype1, 20)
        assert len(ctr.obsels) == 3
        o23 = self.src1.create_obsel("o23", self.otype1, 30)
        assert len(ctr.obsels) == 4
        o11 = self.src1.create_obsel("o11", self.otype1, 10)
        assert len(ctr.obsels) == 5
        o20 = self.src1.create_obsel("o20", self.otype1, 0)
        assert len(ctr.obsels) == 6

        with self.src1.obsel_collection.edit() as editable:
            editable.remove((o10.uri, None, None))
        assert len(ctr.obsels) == 5

        with self.src1.obsel_collection.edit() as editable:
            editable.remove((o21.uri, None, None))
        assert len(ctr.obsels) == 4

    def test_sparql_inherit_all(self):

        sparql = """
          PREFIX : <%s#>
          PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>

          CONSTRUCT {
              [ k:hasSourceObsel ?sobs ] .
          }
          WHERE {
              ?sobs a :ot1 .
          }
        """ % self.model.uri
        ctr = self.base.create_computed_trace("ctr/", KTBS.sparql, {
                                                  "sparql": sparql,
                                                  "inherit": "yes"
                                              }, [self.src1],)

        assert not ctr.diagnosis
        assert ctr.model == self.model
        assert ctr.origin == self.origin
        assert len(ctr.obsels) == 0
        ctr.obsel_collection.force_state_refresh()
        assert ctr.diagnosis == None

        o1 = self.src1.create_obsel("o1", self.otype1, 0,
                                    attributes = {self.atype: "héhé"})
        assert len(self.src1.obsels) == 1
        assert len(ctr.obsels) == 1
        assert ctr.obsels[0].obsel_type == o1.obsel_type
        assert ctr.obsels[0].begin == o1.begin
        assert ctr.obsels[0].end == o1.end
        assert ctr.obsels[0].subject == o1.subject
        assert ctr.obsels[0].get_attribute_value(self.atype) == \
            o1.get_attribute_value(self.atype)

    def test_sparql_inherit_some(self):

        sparql = """
          PREFIX : <%s#>
          PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>

          CONSTRUCT {
              [ k:hasSourceObsel ?sobs ;
                a :ot2 ;
                :at "overridden" ;
                k:hasEnd ?end
              ] .
          }
          WHERE {
              SELECT ?sobs ((?b + 1) as ?end) {
                  ?sobs a :ot1 ; k:hasBegin ?b .
              }
          }
        """ % self.model.uri
        ctr = self.base.create_computed_trace("ctr/", KTBS.sparql, {
                                                  "sparql": sparql,
                                                  "inherit": "yes"
                                              }, [self.src1],)

        assert not ctr.diagnosis
        assert ctr.model == self.model
        assert ctr.origin == self.origin
        assert len(ctr.obsels) == 0
        ctr.obsel_collection.force_state_refresh()
        assert ctr.diagnosis == None

        o1 = self.src1.create_obsel("o1", self.otype1, 0, attributes = {self.atype: "héhé"})
        assert len(self.src1.obsels) == 1
        assert len(ctr.obsels) == 1
        assert ctr.obsels[0].obsel_type == self.otype2
        assert ctr.obsels[0].begin == o1.begin
        assert ctr.obsels[0].end == o1.begin + 1
        assert ctr.obsels[0].subject == o1.subject
        assert ctr.obsels[0].get_attribute_value(self.atype) == "overridden"

    def test_sparql_bad_scope(self):
        sparql = """
        PREFIX : <http://example.org/model#>
        PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>

        CONSTRUCT {
            [ k:hasTrace <%(__destination__)s> ;
              a ?ot ;
              k:hasBegin ?begin ;
              k:hasEnd   ?begin ;
              k:hasSubject "anonymous" ;
              k:hasSourceObsel ?sobs ;
              :at "foo"
            ]
        }
        WHERE {
            ?sobs a ?ot ; k:hasBegin ?begin .
        }
        """

        ctr = self.base.create_computed_trace("ctr/", KTBS.sparql, {
            "sparql": sparql,
            "scope": "foo",
        }, [self.src1], )

        assert ctr.diagnosis is not None

    def test_sparql_scope_store(self):
        sparql = """
        PREFIX : <http://example.org/model#>
        PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>

        CONSTRUCT {
            [ k:hasTrace <%(__destination__)s> ;
              a ?ot ;
              k:hasBegin ?begin ;
              k:hasEnd   ?begin ;
              k:hasSubject "anonymous" ;
              k:hasSourceObsel ?sobs ;
              :at "foo"
            ]
        }
        WHERE {
            ?sobs a ?ot ; k:hasBegin ?begin .
        }
        """

        ctr = self.base.create_computed_trace("ctr/", KTBS.sparql, {
            "sparql": sparql,
            "scope": "store",
        }, [self.src1], )

        assert ctr.diagnosis is not None

    def test_sparql_scope_base(self):
        def test_sparql_inherit_all(self):
            sparql = """
              PREFIX : <%s#>
              PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>

              CONSTRUCT {
                  [ k:hasSourceObsel ?sobs ] .
              }
              WHERE {
                  ?sobs :hasTrace <%(__source__)s> ; a ?obstype .
                  ?obstype a :ObselType .
              }
            """ % self.model.uri
            ctr = self.base.create_computed_trace("ctr/", KTBS.sparql, {
                "sparql": sparql,
                "inherit": "yes",
                "scope": "base"
            }, [self.src1], )

            assert ctr.model == self.model
            assert ctr.origin == self.origin
            assert len(ctr.obsels) == 0
            ctr.obsel_collection.force_state_refresh()
            assert ctr.diagnosis == None

            o1 = self.src1.create_obsel("o1", KTBS.Obsel, 0,
                                        attributes={self.atype: "héhé"})
            assert len(self.src1.obsels) == 1
            assert len(ctr.obsels) == 0


            o2 = self.src1.create_obsel("o2", self.otype1, 1,
                                        attributes={self.atype: "haha"})
            assert len(self.src1.obsels) == 2
            assert len(ctr.obsels) == 1
            assert ctr.obsels[0].obsel_type == o2.obsel_type
            assert ctr.obsels[0].begin == o2.begin
            assert ctr.obsels[0].end == o2.end
            assert ctr.obsels[0].subject == o2.subject
            assert ctr.obsels[0].get_attribute_value(self.atype) == \
                o1.get_attribute_value(self.atype)

            o3 = self.src1.create_obsel("o3", self.otype2, 2,
                                        attributes={self.atype: "hoho"})
            assert len(self.src1.obsels) == 3
            assert len(ctr.obsels) == 2
            assert ctr.obsels[0].obsel_type == o3.obsel_type
            assert ctr.obsels[0].begin == o3.begin
            assert ctr.obsels[0].end == o3.end
            assert ctr.obsels[0].subject == o3.subject
            assert ctr.obsels[0].get_attribute_value(self.atype) == \
                o1.get_attribute_value(self.atype)

    def test_sparql_scope_trace(self):
        def test_sparql_scope_base(self):
            def test_sparql_inherit_all(self):
                sparql = """
                  PREFIX : <%s#>
                  PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>

                  CONSTRUCT {
                      [ k:hasSourceObsel ?sobs ] .
                  }
                  WHERE {
                      ?sobs :hasTrace <%(__source__)s> ; a ?obstype .
                      ?obstype a :ObselType . # only in the model
                  }
                """ % self.model.uri
                ctr = self.base.create_computed_trace("ctr/", KTBS.sparql, {
                    "sparql": sparql,
                    "inherit": "yes",
                    "scope": "trace"
                }, [self.src1], )

                assert ctr.model == self.model
                assert ctr.origin == self.origin
                assert len(ctr.obsels) == 0
                ctr.obsel_collection.force_state_refresh()
                assert ctr.diagnosis == None

                o1 = self.src1.create_obsel("o1", KTBS.Obsel, 0,
                                            attributes={self.atype: "héhé"})
                assert len(self.src1.obsels) == 1
                assert len(ctr.obsels) == 0

                o2 = self.src1.create_obsel("o2", self.otype1, 1,
                                            attributes={self.atype: "haha"})
                assert len(self.src1.obsels) == 2
                assert len(ctr.obsels) == 0

                o3 = self.src1.create_obsel("o3", self.otype2, 2,
                                            attributes={self.atype: "hoho"})
                assert len(self.src1.obsels) == 3
                assert len(ctr.obsels) == 0


class TestIssue28(KtbsTestCase):

    def setup(self):
        super(TestIssue28, self).setup()
        self.base = self.my_ktbs.create_base("b/")
        self.model = self.base.create_model("m")
        self.origin = "orig-abc"
        self.src1 = self.base.create_stored_trace("s1/", self.model,
                                                  origin=self.origin,
                                                  default_subject="alice")

    def test_diagnosis(self):
        ctr1 = self.base.create_computed_trace(
            "c1/", KTBS.sparql,
            {
                u"sparql": u'CONSTRUCT { [ a 42 ] } { ?s a "%()s" }',
                u"hà": u"foo",
            }, [self.src1]
        )
        assert ctr1.diagnosis is not None


    def test_obsel_collection(self):
        ctr1 = self.base.create_computed_trace(
            "c1/", KTBS.sparql,
            {
                u"sparql": u'CONSTRUCT { [ a 42 ] } { ?s a "%()s" }',
                u"hà": u"foo",
            }, [self.src1]
        )
        assert_raises(CanNotProceedError,
                      ctr1.obsel_collection.get_state)

class TestOverrideParameter(KtbsTestCase):

    def setup(self):
        super(TestOverrideParameter, self).setup()
        self.base = self.my_ktbs.create_base("b/")
        model = self.base.create_model("m")
        otype1 = self.otype1 = model.create_obsel_type("#ot1")
        otype2 = self.otype2 = model.create_obsel_type("#ot2")
        src = self.base.create_stored_trace("s/", model, origin="now")
        src.create_obsel(None, otype1)
        src.create_obsel(None, otype2)
        src.create_obsel(None, otype2)
        self.meth1 = self.base.create_method("meth1", KTBS.filter,
                                            {"otypes": otype1.uri})
        self.ctr = self.base.create_computed_trace("ctr/", self.meth1,
                                                   sources=[src])

    def test_overriden_parameter_in_computed_trace(self):
        assert len(self.ctr.obsels) == 1
        self.ctr.set_parameter("otypes", self.otype2.uri)
        assert len(self.ctr.obsels) == 2
        self.ctr.set_parameter("otypes", None)
        assert len(self.ctr.obsels) == 1
        # deleting it a second time should have no effect
        self.ctr.set_parameter("otypes", None)
        assert len(self.ctr.obsels) == 1

    def test_overriden_parameter_in_method(self):
        meth2 = self.base.create_method("meth2", self.meth1,
                                            {"otypes": self.otype2.uri})
        self.ctr.method = meth2
        assert len(self.ctr.obsels) == 2
        self.ctr.set_parameter("otypes", self.otype1.uri)
        assert len(self.ctr.obsels) == 1
        meth2.set_parameter("otypes", None)
        assert len(self.ctr.obsels) == 1
        meth2.set_parameter("otypes", self.otype2.uri)
        assert len(self.ctr.obsels) == 1
        self.ctr.set_parameter("otypes", None)
        assert len(self.ctr.obsels) == 2
        meth2.set_parameter("otypes", None)
        assert len(self.ctr.obsels) == 1
