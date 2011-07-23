from rdfrest.namespaces import RDFREST
from rdfrest.resource import Resource
from rdfrest.service import Service

from rdflib import Graph, Namespace

from nose.tools import raises

# I test the proper work of register/get

NS = Namespace("http://example.org/ns/")
BASE = Namespace("http://localhost:12345/")

class MyService(Service):
    pass

@MyService.register
class A(Resource):
    MAIN_RDF_TYPE = NS.A

@MyService.register
class B(Resource):
    MAIN_RDF_TYPE = NS.B

@MyService.register
class C(Resource):
    MAIN_RDF_TYPE = NS.C

# NOT registered
class D(Resource):
    MAIN_RDF_TYPE = NS.D


# artificially populate a store:

# better way to build the store?
store = Graph().store
    
private_a = Graph(store, BASE["a#private"])
private_a.add((BASE.a, RDFREST.hasImplementation, NS.A))
private_b = Graph(store, BASE["b#private"])
private_b.add((BASE.b, RDFREST.hasImplementation, NS.B))
private_c = Graph(store, BASE["c#private"])
private_c.add((BASE.c, RDFREST.hasImplementation, NS.C))
private_d = Graph(store, BASE["d#private"])
private_d.add((BASE.d, RDFREST.hasImplementation, NS.D))

service = MyService(store)
    
def test_a():
    test_a = service.get(BASE.a)
    assert isinstance(test_a, A), test_a

def test_b():
    test_b = service.get(BASE.b)
    assert isinstance(test_b, B), test_b

def test_c():
    test_c = service.get(BASE.c)
    assert isinstance(test_c, C), test_c

@raises(AssertionError)
def test_d():
    test_d = service.get(BASE.d) # stored but not registered

def test_e():
    test_e = service.get(BASE.e) # not even stored
    assert test_e is None, test_e
