from rdflib import Graph, Namespace, RDF, plugin
from rdflib.store import Store

from rdfrest.mixins import *
from rdfrest.resource import Resource
from rdfrest.service import Service

ROOT = Namespace("http://localhost:12345/")
RNS = Namespace("http://example.org/reserved-ns/")
ONS = Namespace("http://example.org/other-ns/")

class MyService(Service):
    "A test service"

    def __init__(self, uri=None):
        if uri is None:
            uri = ROOT[""]
        else:
            uri = URIRef(uri)
        Service.__init__( self, plugin.get("IOMemory", Store)(), uri)
            

@MyService.register
class Item(WithCardinalityMixin, BookkeepingMixin, WithReservedNamespacesMixin,
          RdfPutMixin, Resource):
    """An example resource."""

    RDF_MAIN_TYPE = RNS.Item

    RDF_RESERVED_NS    = [RNS,]
    RDF_PUTABLE_IN     = [RNS.rw_in,]
    RDF_PUTABLE_OUT    = [RNS.rw_out,]
    RDF_PUTABLE_TYPES  = [RNS.rw_type,]
    RDF_POSTABLE_IN    = [RNS.ro_in, ]
    RDF_POSTABLE_OUT   = [RNS.ro_out,]
    RDF_POSTABLE_TYPES = [RNS.ro_type,]

    RDF_CARDINALITY_IN  = [ (ONS.c1_in,    1, 1),
                            (ONS.c01_in,   0, 1),
                            (ONS.c23_in,   2, 3),
                            (ONS.c1n_in,   1, None),
                            (ONS.c0_in ,   None, 0),
                            ]
    RDF_CARDINALITY_OUT = [ (ONS.c1_out,   1, 1),
                            (ONS.c01_out,  0, 1),
                            (ONS.c23_out,  2, 3),
                            (ONS.c1n_out,  1, None),
                            (ONS.c0_out ,  None, 0),
                            ]

    @classmethod
    def populate(cls, node, parent, graph=None):
        if graph is None:
            graph = Graph()
        graph.add((node,    RDF.type,   cls.RDF_MAIN_TYPE))
        graph.add((parent,  ONS.c1_in,   node))
        graph.add((ONS.foo, ONS.c23_in,  node))
        graph.add((ONS.bar, ONS.c23_in,  node))
        graph.add((ONS.bar, ONS.c1n_in,  node))
        graph.add((ONS.bar, RNS.ro_in,   node))
        graph.add((ONS.bar, RNS.rw_in,   node))
        graph.add((node, ONS.c1_out,    ONS.foo))
        graph.add((node, ONS.c23_out,   ONS.foo))
        graph.add((node, ONS.c23_out,   ONS.bar))
        graph.add((node, ONS.c1n_out,   ONS.bar))
        graph.add((node, RNS.ro_out,    ONS.bar))
        graph.add((node, RNS.rw_out,    ONS.bar))
        return graph



@MyService.register_root
class Folder(Item, RdfPostMixin):
    """An extension of Item, which allows to be posted new resources."""

    RDF_MAIN_TYPE = RNS.Folder

    RDF_RESERVED_NS   = [ONS,]
    RDF_PUTABLE_IN    = [ONS.c1_in,  ONS.c23_in,  ONS.c1n_in]
    RDF_PUTABLE_OUT   = [ONS.c1_out, ONS.c23_out, ONS.c1n_out]

    RDF_CARDINALITY_IN  = [(RNS.rw_in,  1, 1)]
    RDF_CARDINALITY_OUT = [(RNS.rw_out, 1, 1)]

    def rdf_post(self, graph, parameters=None):
        created = super(Folder, self).rdf_post(graph, parameters)
        with self._edit as graph:
            for i in created:
                graph.add((self.uri, RNS.hasChild, i))
        return created

    @classmethod
    def create_root_graph(cls, uri):
        graph = super(Folder, cls).create_root_graph(uri)
        return cls.populate(uri, ONS.foo, graph)
