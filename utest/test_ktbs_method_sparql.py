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

from pytest import raises as assert_raises

from ktbs.namespace import KTBS
from rdfrest.exceptions import CanNotProceedError

from .test_ktbs_engine import KtbsTestCase


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
