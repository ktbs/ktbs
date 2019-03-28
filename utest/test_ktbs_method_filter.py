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

from ktbs.engine.resource import METADATA
from ktbs.methods.filter import LOG as FILTER_LOG
from ktbs.namespace import KTBS

from .test_ktbs_engine import KtbsTestCase

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
        assert get_custom_state(ctr, 'last_seen_u') == str(o10.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 10
        assert get_custom_state(ctr, 'passed_maxtime') == False

        self.log.info(">strictly temporally monotonic change: add o15")
        o15 = src.create_obsel("o15", otype, 15)
        assert len(ctr.obsels) == 2
        assert get_custom_state(ctr, 'last_seen_u') == str(o15.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 15
        assert get_custom_state(ctr, 'passed_maxtime') == False

        self.log.info(">strictly temporally monotonic change: add o20")
        o20 = src.create_obsel("o20", otype, 20)
        assert len(ctr.obsels) == 3
        assert get_custom_state(ctr, 'last_seen_u') == str(o20.uri)
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
        assert get_custom_state(ctr, 'last_seen_u') == str(o00.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 0
        self.log.info(">strictly temporally monotonic change: add o05")
        o05 = src.create_obsel("o05", otype2, 5)
        assert len(ctr.obsels) == 2
        assert get_custom_state(ctr, 'last_seen_u') == str(o05.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 5
        self.log.info(">strictly temporally monotonic change: add o10")
        o10 = src.create_obsel("o10", otype3, 10)
        assert len(ctr.obsels) == 2
        assert get_custom_state(ctr, 'last_seen_u') == str(o10.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 10
        self.log.info(">strictly temporally monotonic change: add o15")
        o15 = src.create_obsel("o15", otype1, 15)
        assert len(ctr.obsels) == 3
        assert get_custom_state(ctr, 'last_seen_u') == str(o15.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 15
        self.log.info(">strictly temporally monotonic change: add o20")
        o20 = src.create_obsel("o20", otype2, 20)
        assert len(ctr.obsels) == 4
        assert get_custom_state(ctr, 'last_seen_u') == str(o20.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 20
        self.log.info(">strictly temporally monotonic change: add o25")
        o25 = src.create_obsel("o25", otype3, 25)
        assert len(ctr.obsels) == 4
        assert get_custom_state(ctr, 'last_seen_u') == str(o25.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 25
        self.log.info(">strictly temporally monotonic change: add o30")
        o30 = src.create_obsel("o30", otype1, 30)
        assert len(ctr.obsels) == 5
        assert get_custom_state(ctr, 'last_seen_u') == str(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30

        self.log.info(">non-temporally monotonic change: add o27")
        o27 = src.create_obsel("o27", otype2, 27)
        assert get_custom_state(ctr, 'last_seen_u') == str(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30
        assert len(ctr.obsels) == 6
        self.log.info(">non-temporally monotonic change: add o17")
        o17 = src.create_obsel("o17", otype1, 17)
        assert len(ctr.obsels) == 7
        assert get_custom_state(ctr, 'last_seen_u') == str(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30
        self.log.info(">non-temporally monotonic change: add o07")
        o07 = src.create_obsel("o07", otype2, 7)
        assert len(ctr.obsels) == 8
        assert get_custom_state(ctr, 'last_seen_u') == str(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30

        self.log.info(">strictly temporally monotonic change: add o35")
        o35 = src.create_obsel("o35", otype1, 35)
        assert len(ctr.obsels) == 9
        assert get_custom_state(ctr, 'last_seen_u') == str(o35.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 35

        self.log.info(">non-monotonic change: removing o15")
        with src.obsel_collection.edit() as editable:
            editable.remove((o15.uri, None, None))
        assert len(ctr.obsels) == 8
        assert get_custom_state(ctr, 'last_seen_u') == str(o35.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 35
        self.log.info(">non-monotonic change: removing o25")
        with src.obsel_collection.edit() as editable:
            editable.remove((o25.uri, None, None))
        assert len(ctr.obsels) == 8
        assert get_custom_state(ctr, 'last_seen_u') == str(o35.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 35
        self.log.info(">non-monotonic change: removing o35")
        with src.obsel_collection.edit() as editable:
            editable.remove((o35.uri, None, None))
        assert len(ctr.obsels) == 7
        assert get_custom_state(ctr, 'last_seen_u') == str(o30.uri)
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


    def test_filter_otypes_inheritance(self):
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype0 = model.create_obsel_type("#ot0")
        otype1 = model.create_obsel_type("#ot1", (otype0,))
        otype2 = model.create_obsel_type("#ot2", (otype0,))
        otype3 = model.create_obsel_type("#ot3")
        src = base.create_stored_trace("s/", model, default_subject="alice")
        ctr = base.create_computed_trace("ctr/", KTBS.filter,
                                         {"otypes": "%s" % (otype0.uri,)},
                                         [src],)

        self.log.info(">strictly temporally monotonic change: add o00")
        o00 = src.create_obsel("o00", otype1, 0)
        assert len(ctr.obsels) == 1
        assert get_custom_state(ctr, 'last_seen_u') == str(o00.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 0
        self.log.info(">strictly temporally monotonic change: add o05")
        o05 = src.create_obsel("o05", otype2, 5)
        assert len(ctr.obsels) == 2
        assert get_custom_state(ctr, 'last_seen_u') == str(o05.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 5
        self.log.info(">strictly temporally monotonic change: add o10")
        o10 = src.create_obsel("o10", otype3, 10)
        assert len(ctr.obsels) == 2
        assert get_custom_state(ctr, 'last_seen_u') == str(o10.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 10
        self.log.info(">strictly temporally monotonic change: add o15")
        o15 = src.create_obsel("o15", otype1, 15)
        assert len(ctr.obsels) == 3
        assert get_custom_state(ctr, 'last_seen_u') == str(o15.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 15
        self.log.info(">strictly temporally monotonic change: add o20")
        o20 = src.create_obsel("o20", otype2, 20)
        assert len(ctr.obsels) == 4
        assert get_custom_state(ctr, 'last_seen_u') == str(o20.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 20
        self.log.info(">strictly temporally monotonic change: add o25")
        o25 = src.create_obsel("o25", otype3, 25)
        assert len(ctr.obsels) == 4
        assert get_custom_state(ctr, 'last_seen_u') == str(o25.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 25
        self.log.info(">strictly temporally monotonic change: add o30")
        o30 = src.create_obsel("o30", otype1, 30)
        assert len(ctr.obsels) == 5
        assert get_custom_state(ctr, 'last_seen_u') == str(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30

        self.log.info(">non-temporally monotonic change: add o27")
        o27 = src.create_obsel("o27", otype2, 27)
        assert get_custom_state(ctr, 'last_seen_u') == str(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30
        assert len(ctr.obsels) == 6
        self.log.info(">non-temporally monotonic change: add o17")
        o17 = src.create_obsel("o17", otype1, 17)
        assert len(ctr.obsels) == 7
        assert get_custom_state(ctr, 'last_seen_u') == str(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30
        self.log.info(">non-temporally monotonic change: add o07")
        o07 = src.create_obsel("o07", otype2, 7)
        assert len(ctr.obsels) == 8
        assert get_custom_state(ctr, 'last_seen_u') == str(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30

        self.log.info(">strictly temporally monotonic change: add o35")
        o35 = src.create_obsel("o35", otype1, 35)
        assert len(ctr.obsels) == 9
        assert get_custom_state(ctr, 'last_seen_u') == str(o35.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 35

        self.log.info(">non-monotonic change: removing o15")
        with src.obsel_collection.edit() as editable:
            editable.remove((o15.uri, None, None))
        assert len(ctr.obsels) == 8
        assert get_custom_state(ctr, 'last_seen_u') == str(o35.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 35
        self.log.info(">non-monotonic change: removing o25")
        with src.obsel_collection.edit() as editable:
            editable.remove((o25.uri, None, None))
        assert len(ctr.obsels) == 8
        assert get_custom_state(ctr, 'last_seen_u') == str(o35.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 35
        self.log.info(">non-monotonic change: removing o35")
        with src.obsel_collection.edit() as editable:
            editable.remove((o35.uri, None, None))
        assert len(ctr.obsels) == 7
        assert get_custom_state(ctr, 'last_seen_u') == str(o30.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 30

    def test_filter_otype_not_in_model(self):
        base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype1 = model.uri + "#ot1";
        otype2 = model.uri + "#ot2";
        src = base.create_stored_trace("s/", model, default_subject="alice")
        ctr = base.create_computed_trace("ctr/", KTBS.filter,
                                         {"otypes": "%s" % (otype1,)},
                                         [src],)

        o00 = src.create_obsel("o00", otype1, 0)
        assert len(ctr.obsels) == 1
        assert get_custom_state(ctr, 'last_seen_u') == str(o00.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 0
        o01 = src.create_obsel("o01", otype2, 1)
        assert len(ctr.obsels) == 1
        assert get_custom_state(ctr, 'last_seen_u') == str(o01.uri)
        assert get_custom_state(ctr, 'last_seen_b') == 1
