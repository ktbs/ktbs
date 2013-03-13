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

from nose.tools import eq_, raises
from unittest import skip

from ktbs.methods.fusion import LOG as FUSION_LOG
from ktbs.methods.filter import LOG as FILTER_LOG
from ktbs.namespace import KTBS, KTBS_NS_URI

from .test_ktbs_engine import KtbsTestCase, HttpKtbsTestCaseMixin


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

        self.log.info(">strictly temporally monotonic change: add o00")
        o00 = src.create_obsel("o00", otype, 0)
        eq_(len(ctr.obsels), 0)
        self.log.info(">strictly temporally monotonic change: add o05")
        o05 = src.create_obsel("o05", otype, 5)
        eq_(len(ctr.obsels), 0)
        self.log.info(">strictly temporally monotonic change: add o10")
        o10 = src.create_obsel("o10", otype, 10)
        eq_(len(ctr.obsels), 1)
        self.log.info(">strictly temporally monotonic change: add o15")
        o15 = src.create_obsel("o15", otype, 15)
        eq_(len(ctr.obsels), 2)
        self.log.info(">strictly temporally monotonic change: add o20")
        o20 = src.create_obsel("o20", otype, 20)
        eq_(len(ctr.obsels), 3)
        self.log.info(">strictly temporally monotonic change: add o25")
        o25 = src.create_obsel("o25", otype, 25)
        eq_(len(ctr.obsels), 3)
        self.log.info(">strictly temporally monotonic change: add o30")
        o30 = src.create_obsel("o30", otype, 30)
        eq_(len(ctr.obsels), 3)

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

        self.log.info(">non-monotonic change: removing o15")
        with src.obsel_collection.edit() as editable:
            editable.remove((o15.uri, None, None))
        eq_(len(ctr.obsels), 3)
        self.log.info(">non-monotonic change: removing o25")
        with src.obsel_collection.edit() as editable:
            editable.remove((o25.uri, None, None))
        eq_(len(ctr.obsels), 3)

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
        self.log.info(">strictly temporally monotonic change: add o05")
        o05 = src.create_obsel("o05", otype2, 5)
        eq_(len(ctr.obsels), 2)
        self.log.info(">strictly temporally monotonic change: add o10")
        o10 = src.create_obsel("o10", otype3, 10)
        eq_(len(ctr.obsels), 2)
        self.log.info(">strictly temporally monotonic change: add o15")
        o15 = src.create_obsel("o15", otype1, 15)
        eq_(len(ctr.obsels), 3)
        self.log.info(">strictly temporally monotonic change: add o20")
        o20 = src.create_obsel("o20", otype2, 20)
        eq_(len(ctr.obsels), 4)
        self.log.info(">strictly temporally monotonic change: add o25")
        o25 = src.create_obsel("o25", otype3, 25)
        eq_(len(ctr.obsels), 4)
        self.log.info(">strictly temporally monotonic change: add o30")
        o30 = src.create_obsel("o30", otype1, 30)
        eq_(len(ctr.obsels), 5)

        self.log.info(">non-temporally monotonic change: add o27")
        o27 = src.create_obsel("o27", otype2, 27)
        eq_(len(ctr.obsels), 6)
        self.log.info(">non-temporally monotonic change: add o17")
        o17 = src.create_obsel("o17", otype1, 17)
        eq_(len(ctr.obsels), 7)
        self.log.info(">non-temporally monotonic change: add o07")
        o07 = src.create_obsel("o07", otype2, 7)
        eq_(len(ctr.obsels), 8)

        self.log.info(">strictly temporally monotonic change: add o35")
        o35 = src.create_obsel("o35", otype1, 35)
        eq_(len(ctr.obsels), 9)

        self.log.info(">non-monotonic change: removing o15")
        with src.obsel_collection.edit() as editable:
            editable.remove((o15.uri, None, None))
        eq_(len(ctr.obsels), 8)
        self.log.info(">non-monotonic change: removing o25")
        with src.obsel_collection.edit() as editable:
            editable.remove((o25.uri, None, None))
        eq_(len(ctr.obsels), 8)
        
          
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

        with src1.obsel_collection.edit() as editable:
            editable.remove((o10.uri, None, None))
        eq_(len(ctr.obsels), 5)

        with src2.obsel_collection.edit() as editable:
            editable.remove((o21.uri, None, None))
        eq_(len(ctr.obsels), 4)
        

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

        with src1.obsel_collection.edit() as editable:
            editable.remove((o10.uri, None, None))
        eq_(len(ctr.obsels), 5)

        with src1.obsel_collection.edit() as editable:
            editable.remove((o21.uri, None, None))
        eq_(len(ctr.obsels), 4)


class TestSparql(KtbsTestCase):

    def __init__(self):
        KtbsTestCase.__init__(self)
    
    def test_sparql_one_source(self):
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype = model.create_obsel_type("#ot")
        atype = model.create_attribute_type("#at")
        origin = "orig-abc"
        src1 = base.create_stored_trace("s1/", model, origin=origin,
                                        default_subject="alice")
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
        ctr = base.create_computed_trace("ctr/", KTBS.sparql, {
                                             "sparql": sparql,
                                             "foo": "bar"
                                         }, [src1],)

        eq_(ctr.model, model)
        eq_(ctr.origin, origin)
        eq_(len(ctr.obsels), 0)

        o10 = src1.create_obsel("o10", otype, 0, attributes = {atype: "héhé"})
        # above, we force some non-ascii output of the script,
        # to check that UTF-8 is corectly decoded by the method
        ctr.obsel_collection.force_state_refresh()
        eq_(ctr.diagnosis, None)

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

        with src1.obsel_collection.edit() as editable:
            editable.remove((o10.uri, None, None))
        eq_(len(ctr.obsels), 5)

        with src1.obsel_collection.edit() as editable:
            editable.remove((o21.uri, None, None))
        eq_(len(ctr.obsels), 4)

    def test_sparql_inherit_all(self):
        
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype1 = model.create_obsel_type("#ot1")
        otype2 = model.create_obsel_type("#ot2")
        atype = model.create_attribute_type("#at")
        origin = "orig-abc"
        src1 = base.create_stored_trace("s1/", model, origin=origin,
                                        default_subject="alice")
        sparql = """
          PREFIX : <%s#>
          PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>

          CONSTRUCT {
              [ k:hasSourceObsel ?sobs ] .
          }
          WHERE {
              ?sobs a :ot1 .
          }
        """ % model.uri
        ctr = base.create_computed_trace("ctr/", KTBS.sparql, {
                                             "sparql": sparql,
                                             "inherit": "yes"
                                         }, [src1],)

        eq_(ctr.model, model)
        eq_(ctr.origin, origin)
        eq_(len(ctr.obsels), 0)
        ctr.obsel_collection.force_state_refresh()
        eq_(ctr.diagnosis, None)

        o1 = src1.create_obsel("o1", otype1, 0, attributes = {atype: "héhé"})
        eq_(len(src1.obsels), 1)
        eq_(len(ctr.obsels), 1)
        eq_(ctr.obsels[0].obsel_type, o1.obsel_type)
        eq_(ctr.obsels[0].begin, o1.begin)
        eq_(ctr.obsels[0].end, o1.end)
        eq_(ctr.obsels[0].subject, o1.subject)
        eq_(ctr.obsels[0].get_attribute_value(atype),
            o1.get_attribute_value(atype))

    def test_sparql_inherit_some(self):
        
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype1 = model.create_obsel_type("#ot1")
        otype2 = model.create_obsel_type("#ot2")
        atype = model.create_attribute_type("#at")
        origin = "orig-abc"
        src1 = base.create_stored_trace("s1/", model, origin=origin,
                                        default_subject="alice")
        sparql = """
          PREFIX : <%s#>
          PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>

          CONSTRUCT {
              [ k:hasSourceObsel ?sobs ;
                a :ot2 ;
                :at "overridden" ;
                k:hasEnd ?end ;
              ] .
          }
          WHERE {
              SELECT ?sobs ((?b + 1) as ?end) {
                  ?sobs a :ot1 ; k:hasBegin ?b .
              }
          }
        """ % model.uri
        ctr = base.create_computed_trace("ctr/", KTBS.sparql, {
                                             "sparql": sparql,
                                             "inherit": "yes"
                                         }, [src1],)

        eq_(ctr.model, model)
        eq_(ctr.origin, origin)
        eq_(len(ctr.obsels), 0)
        ctr.obsel_collection.force_state_refresh()
        eq_(ctr.diagnosis, None)

        o1 = src1.create_obsel("o1", otype1, 0, attributes = {atype: "héhé"})
        eq_(len(src1.obsels), 1)
        eq_(len(ctr.obsels), 1)
        eq_(ctr.obsels[0].obsel_type, otype2)
        eq_(ctr.obsels[0].begin, o1.begin)
        eq_(ctr.obsels[0].end, o1.begin + 1)
        eq_(ctr.obsels[0].subject, o1.subject)
        eq_(ctr.obsels[0].get_attribute_value(atype), "overridden")

