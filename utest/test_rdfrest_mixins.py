# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    RDF-REST is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RDF-REST is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with RDF-REST.  If not, see <http://www.gnu.org/licenses/>.

from nose.tools import assert_raises
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD
from time import sleep
from unittest import skip

import example2 # can not import do_tests directly, nose tries to run it...
from example2 import EXAMPLE, Group2Implementation, Item2Implementation, \
    make_example2_service
from rdfrest.exceptions import InvalidDataError
from rdfrest.factory import unregister_service
from rdfrest.utils import coerce_to_node

OTHER = Namespace("http://example.org/other/")

EXPECTING_LITERAL = (EXAMPLE.label,)

class TestMixins:

    ROOT_URI = URIRef("http://localhost:11235/foo/")
    service = None
    root = None
    item = None

    def setUp(self):
        self.service = make_example2_service(self.ROOT_URI,
                                             additional = [TestItem])
        self.root = self.service.get(self.ROOT_URI,
                                     _rdf_type=EXAMPLE.Group2)
        assert isinstance(self.root, Group2Implementation)
        self.items = []

    def tearDown(self):
        if self.items is not None:
            for i in self.items:
                try:
                    i.delete()
                except:
                    pass
            del self.items
        if self.root is not None:
            del self.root
        if self.service is not None:
            unregister_service(self.service)
            del self.service
    
    def prepare_test_item(self):
        new_graph = Graph()
        bnode = BNode()
        for triple in [(self.root.uri, EXAMPLE.contains, bnode),
                       (bnode, RDF.type, RESERVED.TestItem),
                       (CARD.something1, CARD.card1_in, bnode),
                       (CARD.something1, CARD.card1n_in, bnode),
                       (CARD.something1, CARD.card23_in, bnode),
                       (CARD.something2, CARD.card23_in, bnode),
                       (bnode, CARD.card1_out, CARD.something1),
                       (bnode, CARD.card1n_out, CARD.something1),
                       (bnode, CARD.card23_out, CARD.something1),
                       (bnode, CARD.card23_out, CARD.something2),
                       ]:
            new_graph.add(triple)
        return bnode, new_graph

    def make_test_item(self):
        created, graph = self.prepare_test_item()
        uris = self.root.post_graph(graph, _created=created,
                                    _rdf_type=RESERVED.TestItem)
        ret = self.root.factory(uris[0], _rdf_type=RESERVED.TestItem)
        assert isinstance(ret, TestItem)
        self.items.append(ret)
        return ret

    def test_example2(self):
        """I use the comprehensive test sequence defined in example1.py

        Note that this sequence does not explicitly use the functionalities
        of the :mod:`mixins` module; but at least it shows that "normal"
        functionalities still work when the mix-in classes are used.
        """        
        example2.do_tests(self.root)

    ################################################################
    #
    # BookkeepingMixin tests
    #

    def test_bk_on_created(self):
        assert hasattr(self.root, "iter_etags")
        assert hasattr(self.root, "last_modified")

    def test_bk_changed_on_edit(self):
        old_etag = list(self.root.iter_etags())
        old_lm = self.root.last_modified
        with self.root.edit() as graph:
            sleep(1) # ensures last_modified will actually change
            graph.add((self.root.uri, RDFS.label, Literal("modified")))
        assert list(self.root.iter_etags()) != old_etag
        assert self.root.last_modified > old_lm

    ################################################################
    #
    # WithReservedNamespaceMixin tests
    #

    def test_rns_in_forbidden(self):
        for uri in [RESERVED.creatableOut, RESERVED.creatableType,
                    RESERVED.editableOut, RESERVED.editableType,
                    RESERVED.otherProp, EXAMPLE.otherProp, EXAMPLE.label]:
            # check that we can not create it        
            with assert_raises(InvalidDataError):
                created, graph = self.prepare_test_item()
                graph.add((RESERVED.somethingElse, uri, created))
                self.root.post_graph(graph)

    def test_rns_in_creatable_only(self):
        for uri in [RESERVED.creatableIn]:
            # check that we can create it
            bnode, graph = self.prepare_test_item()
            graph.add((RESERVED.somethingElse, uri, bnode))
            uris = self.root.post_graph(graph)
            item = self.root.factory(uris[0])
            assert isinstance(item, TestItem)
            # check that we can not edit it
            with assert_raises(InvalidDataError):
                with item.edit() as editable:
                    editable.remove((None, uri, item.uri))

    def test_rns_in_editable(self):
        for uri in [RESERVED.editableIn, OTHER.prop ]:
            # check that we can create it
            bnode, graph = self.prepare_test_item()
            graph.add((RESERVED.somethingElse, uri, bnode))
            uris = self.root.post_graph(graph)
            item = self.root.factory(uris[0])
            assert isinstance(item, TestItem)
            # check that we can edit it
            with item.edit() as editable:
                editable.remove((None, uri, item.uri))


    def test_rns_out_forbidden(self):
        for uri in [RESERVED.creatableIn, RESERVED.creatableType,
                    RESERVED.editableIn, RESERVED.editableType,
                    RESERVED.otherProperty, EXAMPLE.otherProp]:
            # check that we can not create it        
            with assert_raises(InvalidDataError):
                created, graph = self.prepare_test_item()
                if uri in EXPECTING_LITERAL:
                    other = Literal("something else")
                else:
                    other = RESERVED.somethingElse
                graph.add((created, uri, other))
                self.root.post_graph(graph)

    def test_rns_out_creatable_only(self):
        for uri in [RESERVED.creatableOut]:
            # check that we can create it
            bnode, graph = self.prepare_test_item()
            if uri in EXPECTING_LITERAL:
                other = Literal("something else")
            else:
                other = RESERVED.somethingElse
            graph.add((bnode, uri, other))
            uris = self.root.post_graph(graph)
            item = self.root.factory(uris[0])
            assert isinstance(item, TestItem)
            # check that we can not edit it
            with assert_raises(InvalidDataError):
                with item.edit() as editable:
                    editable.remove((item.uri, uri, None))

    def test_rns_out_editable(self):
        for uri in [RESERVED.editableOut, EXAMPLE.label, OTHER.prop ]:
            # check that we can create it
            bnode, graph = self.prepare_test_item()
            if uri in EXPECTING_LITERAL:
                other = Literal("something else")
            else:
                other = RESERVED.somethingElse
            graph.add((bnode, uri, other))
            uris = self.root.post_graph(graph)
            item = self.root.factory(uris[0])
            assert isinstance(item, TestItem)
            # check that we can edit it
            with item.edit() as editable:
                editable.remove((item.uri, uri, None))


    def test_rns_type_forbidden(self):
        for uri in [RESERVED.creatableIn, RESERVED.creatableOut,
                    RESERVED.editableIn, RESERVED.editableOut,
                    RESERVED.otherType, EXAMPLE.otherType ]:
            # check that we can not create it        
            with assert_raises(InvalidDataError):
                created, graph = self.prepare_test_item()
                graph.add((created, RDF.type, uri))
                self.root.post_graph(graph)

    def test_rns_type_creatable_only(self):
        for uri in [RESERVED.creatableType]:
            # check that we can create it
            bnode, graph = self.prepare_test_item()
            graph.add((bnode, RDF.type, uri))
            uris = self.root.post_graph(graph)
            item = self.root.factory(uris[0])
            assert isinstance(item, TestItem)
            # check that we can not edit it
            with assert_raises(InvalidDataError):
                with item.edit() as editable:
                    editable.remove((item.uri, RDF.type, uri))

    def test_rns_type_editable(self):
        for uri in [RESERVED.editableType, OTHER.type ]:
            # check that we can create it
            bnode, graph = self.prepare_test_item()
            graph.add((bnode, RDF.type, uri))
            uris = self.root.post_graph(graph)
            item = self.root.factory(uris[0])
            assert isinstance(item, TestItem)
            # check that we can edit it
            with item.edit() as editable:
                editable.remove((item.uri, RDF.type, uri))

    ################################################################
    #
    # WithCardinalityMixin tests
    #

    def test_cardinality(self):
        test_create = self.check_cardinality_create
        test_edit = self.check_cardinality_create

        for prop,             inmin, inmax, outmin, outmax in [
            (CARD.card1_in,   1,     1,     0,      999),
            (CARD.card01_in,  0,     1,     0,      999),
            (CARD.card23_in,  2,     3,     0,      999),
            (CARD.card1n_in,  1,   999,     0,      999),
            (CARD.card0_in,   0,     0,     0,      999),
            (CARD.card1_out,  0,   999,     1,        1),
            (CARD.card01_out, 0,   999,     0,        1),
            (CARD.card23_out, 0,   999,     2,        3),
            (CARD.card1n_out, 0,   999,     1,      999),
            (CARD.card0_out,  0,   999,     0,        0),
            (EXAMPLE.label,   0,     0,     0,        1),
            ]:
            for i in range(4):
                must_pass_in = (inmin <= i <= inmax)
                must_pass_out = (outmin <= i <= outmax)

                for test_proc in [self.check_cardinality_create,
                                  self.check_cardinality_create]:

                    if must_pass_in:
                        test_proc("in", prop, i)
                    else:
                        with assert_raises(InvalidDataError):
                            test_proc("in", prop, i)

                    if must_pass_out:
                        test_proc("out", prop, i)
                    else:
                        with assert_raises(InvalidDataError):
                            test_proc("out", prop, i)


    def check_cardinality_create(self, direction, prop, nb):
        bnode, new_graph = self.prepare_test_item()
        self.change_cardinality_prop(new_graph, bnode, prop, nb, direction)
        uris = self.root.post_graph(new_graph)
        self.root.factory(uris[0]).delete()
        self.root.force_state_refresh()
                             
    def check_cardinality_edit(self, direction, prop, nb):
        bnode, new_graph = self.prepare_test_item()
        uris = self.root.post_graph(new_graph)
        test = self.root.factory(uris[0])
        assert isinstance(item, TestItem)
        with test.edit() as editable:
            self.change_cardinality_prop(editable, test.uri, prop, nb,direction)
        test.delete()
        self.root.force_state_refresh()

    def change_cardinality_prop(self, graph, subject, prop, nb, direction):
        if direction == "in":
            graph.remove((None, prop, subject))
        else: # direction == "out"
            graph.remove((subject, prop, None))
        for i in range(nb):
            if prop == EXAMPLE.label and direction == "out":
                other = Literal("something%s" % (i+1))
            else:
                other = CARD["something%s" % (i+1)]
            if direction == "in":
                graph.add((other, prop, subject))
            else: # direction == "out"
                graph.add((subject, prop, other))

    ################################################################
    #
    # WithTypedPropertiesMixin tests
    #

    def test_typed_properties(self):
        for typed_prop in (Item2Implementation.RDF_TYPED_PROP
                           + TestItem.RDF_TYPED_PROP):
            if len(typed_prop) == 2:
                typed_prop += (None,)
            prop, ntype, vtype = typed_prop

            for val in [Literal("foo"),
                        Literal("foo", lang="en"),
                        Literal("foo", datatype=XSD.string),
                        Literal(42),
                        Literal(3.14),
                        Literal(True),
                        Literal("foo", datatype=TYPED.custom)]:

                testitem = self.make_test_item()
                must_pass = (ntype == "literal"
                             and (vtype is None
                                  or vtype == val.datatype
                                  or (vtype == XSD.string
                                      and val.datatype is None)))
                print prop, val.n3(), must_pass
                if must_pass:
                    with testitem.edit() as editable:
                        editable.add((testitem.uri, prop, val))
                else:
                    with assert_raises(InvalidDataError):
                        with testitem.edit() as editable:
                            editable.add((testitem.uri, prop, val))

            for obj, typ in [(TYPED.other, None),
                             (TYPED.other, TYPED.Foo),
                             (TYPED.other, TYPED.Bar),
                             (BNode(), None),
                             (BNode(), TYPED.Foo),
                             (BNode(), TYPED.Bar)]:

                testitem = self.make_test_item()
                must_pass = (ntype == "uri"
                             and (vtype is None or vtype == typ))
                
                print prop, obj, typ, must_pass
                if must_pass:
                    with testitem.edit() as editable:
                        editable.add((testitem.uri, prop, obj))
                        if typ:
                            editable.add((obj, RDF.type, typ))
                            
                else:
                    with assert_raises(InvalidDataError):
                        with testitem.edit() as editable:
                            editable.add((testitem.uri, prop, obj))
                            if typ:
                                editable.add((obj, RDF.type, typ))


RESERVED = Namespace("http://example.org/reserved#")
CARD = Namespace("http://example.org/cardinality#")
TYPED = Namespace("http://example.org/typed#")

class TestItem(Item2Implementation):
    """A subclass of Item2 for systematical testing of the mixins module.
    """
    RDF_MAIN_TYPE = RESERVED.TestItem

    RDF_RESERVED_NS =     [RESERVED]
    RDF_CREATABLE_IN =    [RESERVED.creatableIn]
    RDF_CREATABLE_OUT =   [RESERVED.creatableOut]
    RDF_CREATABLE_TYPES = [RESERVED.creatableType]
    RDF_EDITABLE_IN =     [RESERVED.editableIn]
    RDF_EDITABLE_OUT =    [RESERVED.editableOut]
    RDF_EDITABLE_TYPES =  [RESERVED.editableType]

    RDF_CARDINALITY_IN = [
        (CARD.card1_in,      1,    1),
        (CARD.card01_in,  None,    1),
        (CARD.card23_in,     2,    3),
        (CARD.card1n_in,     1, None),
        (CARD.card0_in,      0,    0),
        # the last example shows how to forbit a spefic
        # NB (..., 0, 0) is equivalent to (..., None, 0) but is more explicit
        ]
    RDF_CARDINALITY_OUT = [
        (CARD.card1_out,     1,    1),
        (CARD.card01_out, None,    1),
        (CARD.card23_out,    2,    3),
        (CARD.card1n_out,    1, None),
        (CARD.card0_out,     0,    0),
        # NB (..., 0, 0) is equivalent to (..., None, 0) but is more explicit
        ]

    RDF_TYPED_PROP = [
        (TYPED.hasUri,     "uri"),
        (TYPED.hasFoo  ,   "uri",     TYPED.Foo),
        (TYPED.hasLiteral, "literal"),
        (TYPED.hasString,  "literal", XSD.string),
        (TYPED.hasInteger, "literal", XSD.string),
        (TYPED.hasFloat,   "literal", XSD.float),
        (TYPED.hasBoolean, "literal", XSD.boolean),
        (TYPED.hasCustom,  "literal", TYPED.custom),
    ]
