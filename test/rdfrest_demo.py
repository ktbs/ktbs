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
from rdfrest.serializer import bind_prefix
from rdfrest.service import Service


NS = Namespace("http://example.org/")
PREFIXES = """
@prefix : <%(NS)s> .
@prefix rdfs: <%(RDFS)s> .
""" % globals()

class Foo(WithCardinalityMixin, BookkeepingMixin, WithReservedNamespacesMixin,
          RdfPutMixin, Resource):
    """An example resource."""

    RDF_MAIN_TYPE = NS.Foo

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

    RDF_MAIN_TYPE = NS.Bar

    def rdf_post(self, graph):
        created = super(Bar, self).rdf_post(graph)
        with self._edit as graph:
            for i in created:
                graph.add((self.uri, NS.has_child, created[0]))
        return created

    @classmethod
    def create_root_graph(cls, uri):
        graph = super(Bar, cls).create_root_graph(uri)
        graph.add((NS.something, NS.rw_in, uri))
        graph.add((uri, NS.rw_out,
                   Literal("rw_in and rw_out are required properties")))
        return graph

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
FooBarService.register_root(Bar)


def main():
    "The main function of this test"
    HOST = "localhost"
    PORT = 8001
    bind_prefix("", NS)
    store = plugin.get("IOMemory", Store)()
    root_uri = URIRef("http://%s:%s/" % (HOST, PORT))
    service = FooBarService(store, root_uri)
    http = HttpFrontend(service)
    print >> stderr, "===", "Starting server on ", root_uri
    make_server(HOST, PORT, http).serve_forever()
    #make_server(HOST, PORT, http).handle_request()

if __name__ == "__main__":
    main()
