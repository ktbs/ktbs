from rdfrest.namespaces import RDFREST
from rdfrest.resource import Resource
from rdfrest.service import Service
from rdfrest.exceptions import CorruptedStore

from rdflib import Graph, Namespace, plugin
from rdflib.store import Store

from nose.tools import raises, with_setup

# I test the proper work of register/get

NS = Namespace("http://example.org/ns/")
BASE = Namespace("http://localhost:12345/")

class MyService(Service):
    pass

@MyService.register_root
class A(Resource):
    RDF_MAIN_TYPE = NS.A

@MyService.register
class B(Resource):
    RDF_MAIN_TYPE = NS.B

@MyService.register
class C(Resource):
    RDF_MAIN_TYPE = NS.C

# NOT registered
class D(Resource):
    RDF_MAIN_TYPE = NS.D


class TestArtificiallyPopulated(object):

    def setUp(self):
        store = plugin.get("IOMemory", Store)()
        private_a = Graph(store, BASE["a#private"])
        private_a.add((BASE.a, RDFREST.hasImplementation, NS.A))
        private_b = Graph(store, BASE["b#private"])
        private_b.add((BASE.b, RDFREST.hasImplementation, NS.B))
        private_c = Graph(store, BASE["c#private"])
        private_c.add((BASE.c, RDFREST.hasImplementation, NS.C))
        private_d = Graph(store, BASE["d#private"])
        private_d.add((BASE.d, RDFREST.hasImplementation, NS.D))
        self.service = MyService(store, BASE)
            
    def test_a(self):
        test_a = self.service.get(BASE.a)
        assert isinstance(test_a, A), test_a
    
    def test_b(self):
        test_b = self.service.get(BASE.b)
        assert isinstance(test_b, B), test_b
    
    def test_c(self):
        test_c = self.service.get(BASE.c)
        assert isinstance(test_c, C), test_c
    
    @raises(AssertionError)
    def test_d(self):
        test_d = self.service.get(BASE.d) # stored but not registered
    
    def test_e(self):
        test_e = self.service.get(BASE.e) # not even stored
        assert test_e is None, test_e

    @raises(CorruptedStore)
    def test_root(self):
        self.service.root

class TestNaturallyPopulated(object):

    def setUp(self):
        store = plugin.get("IOMemory", Store)()        
        self.service = MyService(store, BASE)

    def test_root(self):
        # do not use the artificial service defined
        root = self.service.root
        assert root is not None
        assert root.uri == BASE[""]
        assert root.service is self.service
        assert self.service.get(BASE[""]) is root
        assert isinstance(root, A)

