from ktbs.local.service import KtbsService
from ktbs.namespaces import KTBS, SKOS

from nose.tools import assert_raises
from rdflib.store import Store
from rdflib import BNode, plugin, Graph, RDF, RDFS
from rdfrest.exceptions import *

class TestKtbsLocal():
    def setUp(self):
        store = plugin.get("IOMemory", Store)()
        self.ktbs = KtbsService(store, "http://localhost:8001/").root

    def tearDown(self):
        self.ktbs = None

    def test_create_two_bases(self):
        base1 = self.ktbs.create_base()
        base2 = self.ktbs.create_base()
        assert base1.uri != base2.uri

    def test_populate(self):
        base1 = self.ktbs.create_base("my 1st base")
        print "base1.uri:", base1.uri
        print "base1.label:", base1.label
        base1.label = "My first base"
        print "base1.label:", base1.label

        model1 = base1.create_model(None,     "generic model")
        model2 = base1.create_model([model1], "specialized model")
        print "model1.uri:", model1.uri
        print "model2.uri:", model2.uri

        my_obsel = model1.create_obsel_type("MyObsel")
        my_spec_obsel = model2.create_obsel_type("MySpecializedObsel",)

        method1 = base1.create_method(KTBS.filter, {"after":1000})
        method2 = base1.create_method(method1, {"before":5000})

        assert 1 # put 0 to check output, 1 to pass unit-test

    def test_post_bad_graph_to_ktbs(self):
        graph = Graph()
        created = BNode()
        graph.add((self.ktbs.uri, KTBS.hasBase, created))
        graph.add((created, RDF.type, RDFS.Resource))
        assert_raises(RdfRestException, self.ktbs.rdf_post, graph)
        graph = Graph()
        created = BNode()
        graph.add((self.ktbs.uri, RDFS.seeAlso, created))
        graph.add((created, RDF.type, KTBS.Base))

    def test_post_bad_graph_to_base(self):
        graph = Graph()
        created = BNode()
        graph.add((self.ktbs.uri, KTBS.hasModel, created))
        graph.add((created, RDF.type, RDFS.Resource))
        assert_raises(RdfRestException, self.ktbs.rdf_post, graph)
        graph = Graph()
        created = BNode()
        graph.add((self.ktbs.uri, RDFS.seeAlso, created))
        graph.add((created, RDF.type, KTBS.hasModel)) # in correct NS
        assert_raises(RdfRestException, self.ktbs.rdf_post, graph)

    def test_create_bad_models(self):
        # checking cardinality constraint on ktbs:contains
        base = self.ktbs.create_base()
        graph = Graph()
        created = BNode()
        graph.add((BNode(), KTBS.contains, created))
        assert_raises(RdfRestException, base.create_model,
                      id=created, graph=graph)

    def test_create_bad_methods(self):
        # bad parameter name
        base = self.ktbs.create_base()
        assert_raises(ValueError, base.create_method, KTBS.filter,
                      {"a=b": "c"})
        # bad parent method (in other base)
        other_base = self.ktbs.create_base()
        method = other_base.create_method(KTBS.filter, {"begin": "1000"})
        assert_raises(ValueError, base.create_method,
                      method, {"end": "5000"})

