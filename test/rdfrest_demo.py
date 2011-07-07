#!/usr/bin/env python
#    This file is part of KTBS <http://liris.cnrs.fr/silex/2009/ktbs>
#    Copyright (C) 2009 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> / SILEX
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
"""
I demonstrate the rdfrest framework with an example server.
"""
from os.path import abspath, dirname, join
from sys import path, stderr

source_dir = dirname(dirname(abspath(__file__)))
lib_dir = join(source_dir, "lib")
path.insert(0, lib_dir)

from  warnings import filterwarnings
#filterwarnings("ignore", category=DeprecationWarning, module="rdflib")
filterwarnings("ignore", category=UserWarning, module="rdflib")

import rdflib
assert rdflib.__version__.startswith("3.")

from rdflib import (ConjunctiveGraph, Graph, Literal, Namespace, plugin, RDF,
                    RDFS, URIRef)
from rdflib.store import Store
from wsgiref.simple_server import make_server

from rdfrest.mixins import (WithCardinalityMixin, WithPreconditionMixin,
                            WithReservedNamespacesMixin,
                            RdfGetMixin, RdfPutMixin, RdfPostMixin,
                            DeleteMixin,
                            )

from rdfrest.resource import Resource
from rdfrest.service import Service


NS = Namespace("http://example.org/")
PREFIXES = """
@prefix : <%(NS)s> .
@prefix rdfs: <%(RDFS)s> .
""" % globals()

class Foo(WithCardinalityMixin, WithPreconditionMixin,
          WithReservedNamespacesMixin, RdfGetMixin, RdfPutMixin, Resource):
    """An example resource."""

    MAIN_RDF_TYPE = NS.Foo

    @classmethod
    def iter_reserved_namespaces(cls):
        for i in super(Foo, cls).iter_puttable_in():
            yield i
        yield NS

    @classmethod
    def iter_puttable_in(cls):
        for i in super(Foo, cls).iter_puttable_in():
            yield i
        yield NS.rw_in

    @classmethod
    def iter_puttable_out(cls):
        for i in super(Foo, cls).iter_puttable_out():
            yield i
        yield NS.rw_out

    @classmethod
    def iter_puttable_types(cls):
        for i in super(Foo, cls).iter_puttable_types():
            yield i
        yield NS.rw_type

    @classmethod
    def iter_postable_in(cls):
        for i in super(Foo, cls).iter_postable_in():
            yield i
        yield NS.ro_in

    @classmethod
    def iter_postable_out(cls):
        for i in super(Foo, cls).iter_postable_out():
            yield i
        yield NS.ro_out

    @classmethod
    def iter_postable_types(cls):
        for i in super(Foo, cls).iter_postable_types():
            yield i
        yield NS.ro_type

    @classmethod
    def iter_cardinality_in(cls):
        for i in super(Foo, cls).iter_cardinality_in():
            yield i
        yield (NS.rw_in, 1, 1)

    @classmethod
    def iter_cardinality_out(cls):
        for i in super(Foo, cls).iter_cardinality_out():
            yield i
        yield (NS.rw_out, 1, 1)


class Bar(Foo, RdfPostMixin):
    """An extension of Foo, which allows to be posted new resources."""

    MAIN_RDF_TYPE = NS.Bar

    def ack_posted(self, posted):
        self.graph.add((self.uri, NS.has_child, posted.uri)) 


class FooBarService(Service):

    def bootstrap(self):
        base = URIRef(self.base)
        g = Graph()
        g.add((base, RDF.type, NS.Bar))
        g.add((base, RDFS.label, Literal("A test service")))
        g.add((base, NS.rw_out, Literal("rw_in and rw_out are required")))
        g.add((NS.something, NS.rw_in, base))
        assert Bar.check_new_graph(None, base, g) is None

        root = Bar(self, base)
        root.init(g)


FooBarService.register(Foo)
FooBarService.register(Bar)


def main():
    config = {}
    base = URIRef("http://localhost:8001/")
    store = plugin.get("IOMemory", Store)()
    config["rdfrest.store"] = store
    config["rdfrest.base"] = str(base)
    service = FooBarService(config)
    service.bootstrap()

    print >>stderr, "===", "Starting server on", base
    make_server("localhost", 8001, service).serve_forever()

if __name__ == "__main__":
    main()
