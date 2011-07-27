from nose.tools import assert_raises, eq_, raises

from rdflib.store import Store
from rdflib import Graph, URIRef, Literal, plugin as rdflib_plugin

from rdfrest.exceptions import *
from rdfrest.resource import Resource
from rdfrest.service import Service


def test_context():
    res = MinimalService().root
    eq_(res.edited, 0)
    eq_(res.touched, 0)
    res.touch()
    eq_(res.edited, 1)
    eq_(res.touched, 1)
    res.touch()
    res.touch()
    eq_(res.edited, 3)
    eq_(res.touched, 3)
    with res._edit:
        res.touch()
        res.touch()
    eq_(res.edited, 4)
    eq_(res.touched, 5)

def test_exception_in_ackedit():
    res = MinimalService().root
    for i in range(4):
        res.touch()
    assert not res.service.rolledback
    # next touch should set self.edited to 5, which raises an exception
    assert_raises(Exception, res.touch)
    assert res.service.rolledback

@raises(InvalidUriError)
def test_no_querystring_as_root():
    res = MinimalService("http://localhost:1234/?a=b")

@raises(InvalidUriError)
def test_no_fragid_as_root():
    res = MinimalService("http://localhost:1234/#a")

class MinimalService(Service):
    def __init__(self, uri=None):
        if uri is None:
            uri = "http://localhost:1234/"
        Service.__init__(
            self,
            rdflib_plugin.get("IOMemory", Store)(),
            URIRef(uri),
            )
        self.store.rollback = self.rollback
        self.rolledback = False

    def rollback(self):
        self.rolledback = True

TOUCHED = URIRef("http://example.org/touched")

@MinimalService.register_root
class MinimalResource(Resource):
    """I do not even support rdf_put, but I can be modified through the 'touch'
    method.
    """

    RDF_MAIN_TYPE = URIRef("http://example.org/Minimal")

    edited = 0

    @property
    def touched(self):
        return self._graph.value(self.uri, TOUCHED).toPython()

    def touch(self):
        with self._edit as graph:
            touched = graph.value(self.uri, TOUCHED).toPython()
            graph.set((self.uri, TOUCHED, Literal(touched + 1)))

    @classmethod
    def create_root_graph(cls, uri):
        graph = super(MinimalResource, cls).create_root_graph(uri)
        graph.set((uri, TOUCHED, Literal(0)))
        return graph

    def ack_edit(self):
        self.edited += 1
        if self.edited == 5:
            raise Exception("testing exceptions in ack_edit")

