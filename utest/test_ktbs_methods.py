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

from json import loads
from nose.tools import assert_raises, eq_
from nose.plugins.skip import SkipTest
from unittest import skip

from ktbs.engine.resource import METADATA
from ktbs.methods.filter import LOG as FILTER_LOG
from ktbs.namespace import KTBS

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

    def __init__(self):
        KtbsTestCase.__init__(self)
        self.log = FILTER_LOG

    def test_filter_temporal(self):
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype = model.create_obsel_type("#ot")
        src = base.create_stored_trace("s/", model, default_subject="alice")
        ctr = base.create_computed_trace("ctr/", KTBS.filter,
                                         {"after": "10", "before": "20"},
                                         [src],)
        eq_(get_custom_state(ctr, 'last_seen'), None)
        eq_(get_custom_state(ctr, 'passed_maxtime'), False)

        self.log.info(">first change (considered non-monotonic): add o00")
        o00 = src.create_obsel("o00", otype, 0)
        eq_(len(ctr.obsels), 0)
        eq_(get_custom_state(ctr, 'last_seen'), None) # not even looked at
        eq_(get_custom_state(ctr, 'passed_maxtime'), False)

        self.log.info(">strictly temporally monotonic change: add o05")
        o05 = src.create_obsel("o05", otype, 5)
        eq_(len(ctr.obsels), 0)
        eq_(get_custom_state(ctr, 'last_seen'), None) # not event looked at
        eq_(get_custom_state(ctr, 'passed_maxtime'), False)

        self.log.info(">strictly temporally monotonic change: add o10")
        o10 = src.create_obsel("o10", otype, 10)
        eq_(len(ctr.obsels), 1)
        eq_(get_custom_state(ctr, 'last_seen'), 10)
        eq_(get_custom_state(ctr, 'passed_maxtime'), False)

        self.log.info(">strictly temporally monotonic change: add o15")
        o15 = src.create_obsel("o15", otype, 15)
        eq_(len(ctr.obsels), 2)
        eq_(get_custom_state(ctr, 'last_seen'), 15)
        eq_(get_custom_state(ctr, 'passed_maxtime'), False)

        self.log.info(">strictly temporally monotonic change: add o20")
        o20 = src.create_obsel("o20", otype, 20)
        eq_(len(ctr.obsels), 3)
        eq_(get_custom_state(ctr, 'last_seen'), 20)
        eq_(get_custom_state(ctr, 'passed_maxtime'), False)

        self.log.info(">strictly temporally monotonic change: add o25")
        o25 = src.create_obsel("o25", otype, 25)
        eq_(len(ctr.obsels), 3)
        eq_(get_custom_state(ctr, 'passed_maxtime'), True)

        self.log.info(">strictly temporally monotonic change: add o30")
        o30 = src.create_obsel("o30", otype, 30)
        eq_(len(ctr.obsels), 3)
        eq_(get_custom_state(ctr, 'passed_maxtime'), True)


        self.log.info(">non-temporally monotonic change: add o27")
        o27 = src.create_obsel("o27", otype, 27)
        eq_(len(ctr.obsels), 3)

        self.log.info(">non-temporally monotonic change: add o17")
        o17 = src.create_obsel("o17", otype, 17)
        eq_(len(ctr.obsels), 4)

        self.log.info(">non-temporally monotonic change: add o07")
        o07 = src.create_obsel("o07", otype, 7)
        eq_(len(ctr.obsels), 4)


        self.log.info(">strictly temporally monotonic change: add o35")
        o35 = src.create_obsel("o35", otype, 35)
        eq_(len(ctr.obsels), 4)
        eq_(get_custom_state(ctr, 'passed_maxtime'), True)


        self.log.info(">non-monotonic change: removing o15")
        o15.delete()
        eq_(len(ctr.obsels), 3)
        eq_(get_custom_state(ctr, 'passed_maxtime'), True)

        self.log.info(">non-monotonic change: removing o25")
        o25.delete()
        eq_(len(ctr.obsels), 3)
        eq_(get_custom_state(ctr, 'passed_maxtime'), True)


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
        eq_(len(ctr.obsels), 0)
        o9_15 = src.create_obsel("o9_15", otype, 9, 15)
        eq_(len(ctr.obsels), 0)
        o10_15 = src.create_obsel("o10_15", otype, 10, 15)
        eq_(len(ctr.obsels), 1)
        o11_15 = src.create_obsel("o11_15", otype, 11, 15)
        eq_(len(ctr.obsels), 2)
        o13_15 = src.create_obsel("o13_15", otype, 13, 15)
        eq_(len(ctr.obsels), 3)
        o13_15a = src.create_obsel("o13_15a", otype, 13, 15)
        eq_(len(ctr.obsels), 4)
        o15_15 = src.create_obsel("o15_15", otype, 15, 15)
        eq_(len(ctr.obsels), 5)
        o15_17 = src.create_obsel("o15_17", otype, 15, 17)
        eq_(len(ctr.obsels), 6)
        o15_20 = src.create_obsel("o15_20", otype, 15, 20)
        eq_(len(ctr.obsels), 7)
        o15_21 = src.create_obsel("o15_21", otype, 15, 21)
        eq_(len(ctr.obsels), 7)
        eq_(get_custom_state(ctr, 'passed_maxtime'), True)
        o15_19 = src.create_obsel("o15_19", otype, 15, 19)
        eq_(len(ctr.obsels), 8)
        eq_(get_custom_state(ctr, 'passed_maxtime'), True)
        o15_21.delete()
        eq_(len(ctr.obsels), 8)
        eq_(get_custom_state(ctr, 'passed_maxtime'), False)


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
        eq_(len(ctr.obsels), 1)
        eq_(get_custom_state(ctr, 'last_seen'), 0)
        self.log.info(">strictly temporally monotonic change: add o05")
        o05 = src.create_obsel("o05", otype2, 5)
        eq_(len(ctr.obsels), 2)
        eq_(get_custom_state(ctr, 'last_seen'), 5)
        self.log.info(">strictly temporally monotonic change: add o10")
        o10 = src.create_obsel("o10", otype3, 10)
        eq_(len(ctr.obsels), 2)
        eq_(get_custom_state(ctr, 'last_seen'), 10)
        self.log.info(">strictly temporally monotonic change: add o15")
        o15 = src.create_obsel("o15", otype1, 15)
        eq_(len(ctr.obsels), 3)
        eq_(get_custom_state(ctr, 'last_seen'), 15)
        self.log.info(">strictly temporally monotonic change: add o20")
        o20 = src.create_obsel("o20", otype2, 20)
        eq_(len(ctr.obsels), 4)
        eq_(get_custom_state(ctr, 'last_seen'), 20)
        self.log.info(">strictly temporally monotonic change: add o25")
        o25 = src.create_obsel("o25", otype3, 25)
        eq_(len(ctr.obsels), 4)
        eq_(get_custom_state(ctr, 'last_seen'), 25)
        self.log.info(">strictly temporally monotonic change: add o30")
        o30 = src.create_obsel("o30", otype1, 30)
        eq_(len(ctr.obsels), 5)
        eq_(get_custom_state(ctr, 'last_seen'), 30)

        self.log.info(">non-temporally monotonic change: add o27")
        o27 = src.create_obsel("o27", otype2, 27)
        eq_(get_custom_state(ctr, 'last_seen'), 30)
        eq_(len(ctr.obsels), 6)
        self.log.info(">non-temporally monotonic change: add o17")
        o17 = src.create_obsel("o17", otype1, 17)
        eq_(len(ctr.obsels), 7)
        eq_(get_custom_state(ctr, 'last_seen'), 30)
        self.log.info(">non-temporally monotonic change: add o07")
        o07 = src.create_obsel("o07", otype2, 7)
        eq_(len(ctr.obsels), 8)
        eq_(get_custom_state(ctr, 'last_seen'), 30)

        self.log.info(">strictly temporally monotonic change: add o35")
        o35 = src.create_obsel("o35", otype1, 35)
        eq_(len(ctr.obsels), 9)
        eq_(get_custom_state(ctr, 'last_seen'), 35)

        self.log.info(">non-monotonic change: removing o15")
        o15.delete()
        eq_(len(ctr.obsels), 8)
        eq_(get_custom_state(ctr, 'last_seen'), 35)
        self.log.info(">non-monotonic change: removing o25")
        o25.delete()
        eq_(len(ctr.obsels), 8)
        eq_(get_custom_state(ctr, 'last_seen'), 35)
        self.log.info(">non-monotonic change: removing o35")
        o35.delete()
        eq_(len(ctr.obsels), 7)
        eq_(get_custom_state(ctr, 'last_seen'), 30)


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
        eq_(len(ctr.obsels), 0)

        def count_relations():
            results = self.service.query("""
                SELECT (COUNT(?x) as ?nr) {
                  GRAPH ?obs { ?obs :hasTrace ?ctr. ?x m:rt ?y }
                }
                """,
                initNs={'': KTBS, 'm': model.uri+"#"},
                initBindings={'ctr': ctr.uri},
            )
            return int(next(iter(results))[0])

        o10 = src.create_obsel("o10", otype, 10, relations=[(rtype, o00)])
        eq_(len(ctr.obsels), 1)
        eq_(count_relations(), 0)
        o11 = src.create_obsel("o11", otype, 11, inverse_relations=[(o05, rtype)])
        eq_(len(ctr.obsels), 2)
        eq_(count_relations(), 0)
        o12 = src.create_obsel("o12", otype, 12, relations=[(rtype, o25)])
        eq_(len(ctr.obsels), 3)
        eq_(count_relations(), 0)
        o13 = src.create_obsel("o13", otype, 13, inverse_relations=[(o30, rtype)])
        eq_(len(ctr.obsels), 4)
        eq_(count_relations(), 0)
        o14 = src.create_obsel("o14", otype, 14, relations=[(rtype, o12)])
        eq_(len(ctr.obsels), 5)
        eq_(count_relations(), 1)
        o15 = src.create_obsel("o15", otype, 15, inverse_relations=[(o13, rtype)])
        eq_(len(ctr.obsels), 6)
        eq_(count_relations(), 2)

          
class TestFusion(KtbsTestCase):

    def __init__(self):
        KtbsTestCase.__init__(self)
    
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

        eq_(ctr.model, model)
        eq_(ctr.origin, origin)
        eq_(len(ctr.obsels), 0)

        o10 = src1.create_obsel("o10", otype, 0)
        eq_(len(ctr.obsels), 1)
        o21 = src2.create_obsel("o21", otype, 10)
        eq_(len(ctr.obsels), 2)
        o12 = src1.create_obsel("o12", otype, 20)
        eq_(len(ctr.obsels), 3)
        o23 = src2.create_obsel("o23", otype, 30)
        eq_(len(ctr.obsels), 4)
        o11 = src1.create_obsel("o11", otype, 10)
        eq_(len(ctr.obsels), 5)
        o20 = src2.create_obsel("o20", otype, 0)
        eq_(len(ctr.obsels), 6)

        o10.delete()
        eq_(len(ctr.obsels), 5)

        o21.delete()
        eq_(len(ctr.obsels), 4)
        

@SkipTest  #@skip("External method has not been upgraded in branch 'raphael'")
class TestExternal(KtbsTestCase):

    def __init__(self):
        KtbsTestCase.__init__(self)

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

        eq_(ctr.model, model)
        eq_(ctr.origin, origin)
        eq_(len(ctr.obsels), 0)
        
    
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

        eq_(ctr.model, model)
        eq_(ctr.origin, origin)
        eq_(len(ctr.obsels), 0)

        o10 = src1.create_obsel("o10", otype, 0)
        eq_(len(ctr.obsels), 1)
        o21 = src1.create_obsel("o21", otype, 10)
        eq_(len(ctr.obsels), 2)
        o12 = src1.create_obsel("o12", otype, 20)
        eq_(len(ctr.obsels), 3)
        o23 = src1.create_obsel("o23", otype, 30)
        eq_(len(ctr.obsels), 4)
        o11 = src1.create_obsel("o11", otype, 10)
        eq_(len(ctr.obsels), 5)
        o20 = src1.create_obsel("o20", otype, 0)
        eq_(len(ctr.obsels), 6)

        o10.delete()
        eq_(len(ctr.obsels), 5)

        o21.delete()
        eq_(len(ctr.obsels), 4)


@SkipTest  #@skip("SPARQL method has not been upgraded in branch 'raphael'")
class TestSparql(KtbsTestCase):

    def __init__(self):
        KtbsTestCase.__init__(self)
        
    def setUp(self):
        super(TestSparql, self).setUp()
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

        eq_(ctr.model, self.model)
        eq_(ctr.origin, self.origin)
        eq_(len(ctr.obsels), 0)

        o10 = self.src1.create_obsel("o10", self.otype1, 0,
                                     attributes = {self.atype: "héhé"})
        # above, we force some non-ascii output of the script,
        # to check that UTF-8 is corectly decoded by the method
        ctr.obsel_collection.force_state_refresh()
        eq_(ctr.diagnosis, None)

        eq_(len(ctr.obsels), 1)
        o21 = self.src1.create_obsel("o21", self.otype1, 10)
        eq_(len(ctr.obsels), 2)
        o12 = self.src1.create_obsel("o12", self.otype1, 20)
        eq_(len(ctr.obsels), 3)
        o23 = self.src1.create_obsel("o23", self.otype1, 30)
        eq_(len(ctr.obsels), 4)
        o11 = self.src1.create_obsel("o11", self.otype1, 10)
        eq_(len(ctr.obsels), 5)
        o20 = self.src1.create_obsel("o20", self.otype1, 0)
        eq_(len(ctr.obsels), 6)

        o10.delete()
        eq_(len(ctr.obsels), 5)

        o21.delete()
        eq_(len(ctr.obsels), 4)

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

        eq_(ctr.model, self.model)
        eq_(ctr.origin, self.origin)
        eq_(len(ctr.obsels), 0)
        ctr.obsel_collection.force_state_refresh()
        eq_(ctr.diagnosis, None)

        o1 = self.src1.create_obsel("o1", self.otype1, 0,
                                    attributes = {self.atype: "héhé"})
        eq_(len(self.src1.obsels), 1)
        eq_(len(ctr.obsels), 1)
        eq_(ctr.obsels[0].obsel_type, o1.obsel_type)
        eq_(ctr.obsels[0].begin, o1.begin)
        eq_(ctr.obsels[0].end, o1.end)
        eq_(ctr.obsels[0].subject, o1.subject)
        eq_(ctr.obsels[0].get_attribute_value(self.atype),
            o1.get_attribute_value(self.atype))

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

        eq_(ctr.model, self.model)
        eq_(ctr.origin, self.origin)
        eq_(len(ctr.obsels), 0)
        ctr.obsel_collection.force_state_refresh()
        eq_(ctr.diagnosis, None)

        o1 = self.src1.create_obsel("o1", self.otype1, 0, attributes = {self.atype: "héhé"})
        eq_(len(self.src1.obsels), 1)
        eq_(len(ctr.obsels), 1)
        eq_(ctr.obsels[0].obsel_type, self.otype2)
        eq_(ctr.obsels[0].begin, o1.begin)
        eq_(ctr.obsels[0].end, o1.begin + 1)
        eq_(ctr.obsels[0].subject, o1.subject)
        eq_(ctr.obsels[0].get_attribute_value(self.atype), "overridden")

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

            eq_(ctr.model, self.model)
            eq_(ctr.origin, self.origin)
            eq_(len(ctr.obsels), 0)
            ctr.obsel_collection.force_state_refresh()
            eq_(ctr.diagnosis, None)

            o1 = self.src1.create_obsel("o1", KTBS.Obsel, 0,
                                        attributes={self.atype: "héhé"})
            eq_(len(self.src1.obsels), 1)
            eq_(len(ctr.obsels), 0)


            o2 = self.src1.create_obsel("o2", self.otype1, 1,
                                        attributes={self.atype: "haha"})
            eq_(len(self.src1.obsels), 2)
            eq_(len(ctr.obsels), 1)
            eq_(ctr.obsels[0].obsel_type, o2.obsel_type)
            eq_(ctr.obsels[0].begin, o2.begin)
            eq_(ctr.obsels[0].end, o2.end)
            eq_(ctr.obsels[0].subject, o2.subject)
            eq_(ctr.obsels[0].get_attribute_value(self.atype),
                o1.get_attribute_value(self.atype))

            o3 = self.src1.create_obsel("o3", self.otype2, 2,
                                        attributes={self.atype: "hoho"})
            eq_(len(self.src1.obsels), 3)
            eq_(len(ctr.obsels), 2)
            eq_(ctr.obsels[0].obsel_type, o3.obsel_type)
            eq_(ctr.obsels[0].begin, o3.begin)
            eq_(ctr.obsels[0].end, o3.end)
            eq_(ctr.obsels[0].subject, o3.subject)
            eq_(ctr.obsels[0].get_attribute_value(self.atype),
                o1.get_attribute_value(self.atype))

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

                eq_(ctr.model, self.model)
                eq_(ctr.origin, self.origin)
                eq_(len(ctr.obsels), 0)
                ctr.obsel_collection.force_state_refresh()
                eq_(ctr.diagnosis, None)

                o1 = self.src1.create_obsel("o1", KTBS.Obsel, 0,
                                            attributes={self.atype: "héhé"})
                eq_(len(self.src1.obsels), 1)
                eq_(len(ctr.obsels), 0)

                o2 = self.src1.create_obsel("o2", self.otype1, 1,
                                            attributes={self.atype: "haha"})
                eq_(len(self.src1.obsels), 2)
                eq_(len(ctr.obsels), 0)

                o3 = self.src1.create_obsel("o3", self.otype2, 2,
                                            attributes={self.atype: "hoho"})
                eq_(len(self.src1.obsels), 3)
                eq_(len(ctr.obsels), 0)
