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

SOURCE_DIR = dirname(dirname(abspath(__file__)))
LIB_DIR = join(SOURCE_DIR, "lib")
path.insert(0, LIB_DIR)

from warnings import filterwarnings
#filterwarnings("ignore", category=DeprecationWarning, module="rdflib")
filterwarnings("ignore", category=UserWarning, module="rdflib")

import rdflib
assert rdflib.__version__.startswith("3.")

from rdflib import (Graph, Literal, Namespace, plugin, RDF, RDFS, URIRef)
from rdflib.store import Store
from wsgiref.simple_server import make_server

from rdfrest.http_front import HttpFrontend
from rdfrest.mixins import (WithCardinalityMixin, BookkeepingMixin,
                            WithReservedNamespacesMixin,
                            RdfPutMixin, RdfPostMixin,
                            )
from rdfrest.resource import Resource
from rdfrest.service import Service


NS = Namespace("http://example.org/")
PREFIXES = """
@prefix : <%(NS)s> .
@prefix rdfs: <%(RDFS)s> .
""" % globals()

class Foo(WithCardinalityMixin, BookkeepingMixin, WithReservedNamespacesMixin,
          RdfPutMixin, Resource):
    """An example resource."""

    MAIN_RDF_TYPE = NS.Foo

    RDF_RESERVED_NS   = [NS,]
    RDF_PUTABLE_IN    = [NS.rw_in,]
    RDF_PUTABLE_OUT   = [NS.rw_out,]
    RDF_PUTABLE_TYPE  = [NS.rw_type,]
    RDF_POSTABLE_IN   = [NS.ro_in,]
    RDF_POSTABLE_OUT  = [NS.ro_out,]
    RDF_POSTABLE_TYPE = [NS.ro_type,]

    RDF_CARDINALITY_IN  = [(NS.rw_in,  1, 1)]
    RDF_CARDINALITY_OUT = [(NS.rw_out, 1, 1)]


class Bar(Foo, RdfPostMixin):
    """An extension of Foo, which allows to be posted new resources."""

    MAIN_RDF_TYPE = NS.Bar

    def ack_created(self, created):
        self._graph.add((self.uri, NS.has_child, created.uri))

class FooBarService(Service):
    "A demo service"

    def bootstrap(self, uri):
        "A method for initializing the root resource in the service"
        graph = Graph()
        graph.add((uri, RDF.type, NS.Bar))
        graph.add((uri, RDFS.label, Literal("A test service")))
        graph.add((uri, NS.rw_out, Literal("rw_in and rw_out are required")))
        graph.add((NS.something, NS.rw_in, uri))
        return Bar.create(self, uri, graph)

FooBarService.register(Foo)
FooBarService.register(Bar)


def main():
    "The main function of this test"
    store = plugin.get("IOMemory", Store)()
    service = FooBarService(store)
    base = URIRef("http://localhost:8001/")
    _root = service.bootstrap(base)
    http = HttpFrontend(service)
    print >> stderr, "===", "Starting server on", base
    #make_server("localhost", 8001, http).handle_request()
    make_server("localhost", 8001, http).serve_forever()

if __name__ == "__main__":
    main()
