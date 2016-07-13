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

from json import dumps
from rdflib import Graph, Literal, Namespace, RDF, URIRef

from ktbs.methods.translation import LOG as TRANS_LOG
from ktbs.namespace import KTBS

from .test_ktbs_engine import KtbsTestCase
from .test_ktbs_methods import get_custom_state

EX = Namespace("http://example.org/")

class TestTranslation(KtbsTestCase):

    def __init__(self):
        KtbsTestCase.__init__(self)
        self.log = TRANS_LOG

    def test_translation(self):
        base = self.my_ktbs.create_base("b/")
        m1 = base.create_model("m1")
        ot1 = m1.create_obsel_type("#ot1")
        ot2 = m1.create_obsel_type("#ot2")
        at1 = m1.create_attribute_type("#at1")
        m2 = base.create_model("m2")
        otA = m2.create_obsel_type("#otA")
        otB = m2.create_obsel_type("#otB")
        atA = m2.create_attribute_type("#atA")

        map = {
            "#ot1": "#otA",
            "#ot2": "#otB",
            "#at1": "#atA",
            "http://example.org/foo": "http://example.org/bar",
            "http://example.org/toto": "http://example.org/tata",
        }
        src = base.create_stored_trace("s/", m1, default_subject="alice")
        ctr = base.create_computed_trace("ctr/", KTBS.translation,
                                         {"model": m2.uri, "map": dumps(map)},
                                         [src],)
        assert get_custom_state(ctr, 'map') == {
            "http://localhost:12345/b/m1#ot1": "http://localhost:12345/b/m2#otA",
            "http://localhost:12345/b/m1#ot2": "http://localhost:12345/b/m2#otB",
            "http://localhost:12345/b/m1#at1": "http://localhost:12345/b/m2#atA",
            "http://example.org/foo": "http://example.org/bar",
            "http://example.org/toto": "http://example.org/tata",
        }
        assert get_custom_state(ctr, 'last_seen') == None

        self.log.info(">first change (considered non-monotonic): add o00")
        o00 = src.create_obsel("o00", ot1, 0)
        assert len(ctr.obsels) == 1
        assert get_custom_state(ctr, 'last_seen') == unicode(o00.uri)
        tst = ctr.get_obsel("o00")
        assert tst.obsel_type == otA, ctr.obsels[-1].state.serialize(format="n3")


        o99 = src.create_obsel("o99", ot2, 99, attributes={at1: Literal(42)})
        assert len(ctr.obsels) == 2
        assert get_custom_state(ctr, 'last_seen') == unicode(o99.uri)
        tst = ctr.get_obsel("o99")
        assert tst.obsel_type == otB
        assert tst.get_attribute_value(atA) == 42


        o50uri = URIRef("o50", src.uri)
        g = Graph()
        g.addN([
            (o50uri, KTBS.hasTrace, src.uri, g),
            (o50uri, KTBS.hasBegin, Literal(50), g),
            (o50uri, RDF.type, ot1.uri, g),
            (o50uri, at1.uri, EX.foo, g),
            (EX.foo, RDF.type, EX.Foo, g),
            (EX.foo, EX.toto, EX.baz, g),
        ])
        o50 = src.post_graph(g)
        assert len(ctr.obsels) == 3
        assert get_custom_state(ctr, 'last_seen') == unicode(o99.uri)
        tst = ctr.get_obsel("o50")
        for triple in [
            (tst.uri, RDF.type, otA.uri),
            (tst.uri, KTBS.hasBegin, Literal(50)),
            (tst.uri, atA.uri, EX.bar),
            (EX.bar, RDF.type, EX.Foo),
            (EX.bar, EX.tata, EX.baz),
        ]:
            assert triple in tst.state, unicode(triple) + "===\n" + tst.state.serialize(format="n3")

