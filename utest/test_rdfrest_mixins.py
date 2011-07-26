from functools import wraps
from nose.tools import assert_raises, with_setup
from time import sleep

from rdfrest.mixins import *
from rdfrest.resource import Resource
from rdfrest.service import Service
from rdfrest.exceptions import *

from rdflib import Graph, Namespace, RDF, RDFS, plugin
from rdflib.compare import graph_diff
from rdflib.store import Store


from rdfrest_example import Folder, Item, MyService, ONS, RNS, ROOT

class TestRootOnly(object):
    """Tests on a service with only a root."""

    def setUp(self):
        self.service = MyService()
    

    def _test_post_uri(self, cls, uri):
        """Abstract test. Called below with Item and Folder."""
        root = self.service.root
        graph = cls.populate(uri, root.uri)
        created = root.rdf_post(graph)
        assert isinstance(created, list)
        assert len(created) == 1
        got_uri = created[0]
        assert got_uri == uri
        got = self.service.get(uri)
        assert got is not None
        assert isinstance(got, cls)
        assert_same_graph(graph, got.rdf_get())
    
        root_graph = mutable_copy(root.rdf_get())
        root_graph.add((root.uri, RNS.hasChild, uri))
        assert_same_graph(root_graph, root.rdf_get())

    def test_post_item_uri(self):
        self._test_post_uri(Item, ROOT.i1)

    def test_post_folder_uri(self):
        self._test_post_uri(Folder, ROOT["f1/"])
    
    def test_post_folder_bad_uri(self):
        # posting a URI without a trailing slash
        root = self.service.root
        folder_graph = Folder.populate(ROOT.g1, root.uri)
        with assert_raises(InvalidDataError):
            root.rdf_post(folder_graph)

    def _test_post_bnode(self, cls):
        """Abstract test. Called below with Item and Folder."""
        root = self.service.root
        graph = cls.populate(BNode(), root.uri)
        created = root.rdf_post(graph)
    
        assert isinstance(created, list)
        assert len(created) == 1
        uri = created[0]
        assert isinstance(uri, URIRef)
        graph = cls.populate(uri, root.uri)
        got = self.service.get(uri)
        assert got is not None
        assert isinstance(got, cls)
        assert_same_graph(graph, got.rdf_get())
    
        root_graph = mutable_copy(root.rdf_get())
        root_graph.add((root.uri, RNS.hasChild, uri))
        assert_same_graph(root_graph, root.rdf_get())

    def test_post_item_bnode(self):
        self._test_post_bnode(Item)

    def test_post_folder_bnode(self):
        self._test_post_bnode(Folder)

    def _test_post_postable_type(self, cls):
        """Abstract test. Called below with Item and Folder."""
        root = self.service.root
        graph = cls.populate(BNode(), root.uri)
        graph.add((graph, RDF.type, RNS.ro_type))
        root.rdf_post(graph)

    def test_post_item_postable_type(self):
        self._test_post_postable_type(Item)
        
    def test_post_folder_postable_type(self):
        self._test_post_postable_type(Folder)
        
    def _test_post_reserved(self, cls):
        """Abstract test. Called below with Item and Folder."""
        root = self.service.root
        root_graph = mutable_copy(root.rdf_get())
        bnode = BNode()
    
        # testing in
        graph = cls.populate(bnode, root.uri)
        graph.add((ONS.foo, RNS.unallowed, bnode))
        with assert_raises(InvalidDataError):
            root.rdf_post(graph)
        # testing out
        graph = cls.populate(bnode, root.uri)
        graph.add((bnode, RNS.unallowed, ONS.foo))
        with assert_raises(InvalidDataError):
            root.rdf_post(graph)
        # testing type
        graph = cls.populate(bnode, root.uri)
        graph.add((bnode, RDF.type, RNS.unallowed))
        with assert_raises(InvalidDataError):
            root.rdf_post(graph)
             
    def test_post_item_reserved(self):
        self._test_post_reserved(Item)

    def test_post_folder_reserved(self):
        self._test_post_reserved(Folder)

    def _test_post_wrong_dir(self, cls):
        """Abstract test. Called below with Item and Folder."""
        root = self.service.root
        root_graph = mutable_copy(root.rdf_get())
        bnode = BNode()
    
        # testing in
        graph = cls.populate(ROOT.i1, root.uri)
        graph.add((ONS.foo, RNS.rw_out, ROOT.i1))
        with assert_raises(InvalidDataError):
            root.rdf_post(graph)
        # testing out
        graph = cls.populate(ROOT.i1, root.uri)
        graph.add((ROOT.i1, RNS.rw_in, ONS.foo))
        with assert_raises(InvalidDataError):
            root.rdf_post(graph)

    def test_post_item_wrong_dir(self):
        self._test_post_wrong_dir(Item)
             
    def test_post_folder_wrong_dir(self):
        self._test_post_wrong_dir(Folder)

    
class _TestWithOneElement(object):
    """Abstract class for tests with a service with one root and one element.

    Subclassed below as TestWithOneItem and TestWithOneFolder.
    """

    uri = None # override in subclasses
    cls = None # override in subclasses


    def setUp(self):
        self.service = MyService()
        graph = self.cls.populate(self.uri, self.service.root.uri)
        self.service.root.rdf_post(graph)
    
    def test_get(self):
        ref = self.cls.populate(self.uri, self.service.root.uri)
        got = self.service.get(self.uri)
        assert_same_graph(ref, got.rdf_get())
        assert_same_graph(got._graph, got.rdf_get())
    
    def test_put_idem(self):
        ref = self.cls.populate(self.uri, self.service.root.uri)
        got = self.service.get(self.uri)
        got.rdf_put(mutable_copy(got.rdf_get()))
        assert_same_graph(ref, got.rdf_get())
    
    def test_put_different(self):
        got = self.service.get(self.uri)
        graph = mutable_copy(got.rdf_get())
        graph.add((self.uri, RDFS.label, Literal("hello")))
        got.rdf_put(graph)
        assert_same_graph(graph, got.rdf_get())
        
    def test_put_reserved(self):
        i1 = self.service.get(self.uri)
        # testing in
        graph = mutable_copy(i1.rdf_get())
        graph.add((ONS.foo, RNS.rw_unallowed, i1.uri))
        with assert_raises(InvalidDataError):
            i1.rdf_put(graph)
        # testing out
        graph = mutable_copy(i1.rdf_get())
        graph.add((i1.uri, RNS.unallowed, ONS.foo))
        with assert_raises(InvalidDataError):
            i1.rdf_put(graph)
        # testing reserved type
        graph = mutable_copy(i1.rdf_get())
        graph.add((i1.uri, RDF.type, RNS.unallowed))
        with assert_raises(InvalidDataError):
            i1.rdf_put(graph)
    
    def test_put_postable(self):
        i1 = self.service.get(self.uri)
        # testing in
        graph = mutable_copy(i1.rdf_get())
        graph.add((ONS.foo, RNS.ro_in, i1.uri))
        with assert_raises(InvalidDataError):
            i1.rdf_put(graph)
        # testing out
        graph = mutable_copy(i1.rdf_get())
        graph.add((i1.uri, RNS.ro_out, ONS.foo))
        with assert_raises(InvalidDataError):
            i1.rdf_put(graph)
        # testing type
        graph = mutable_copy(i1.rdf_get())
        graph.add((i1.uri, RDF.type, RNS.ro_type))
        with assert_raises(InvalidDataError):
            i1.rdf_put(graph)
        # testing main type
        graph = mutable_copy(i1.rdf_get())
        graph.remove((i1.uri, RDF.type, self.cls.RDF_MAIN_TYPE))
        with assert_raises(InvalidDataError):
            i1.rdf_put(graph)
    
    def test_put_wrong_dir(self):
        i1 = self.service.get(self.uri)
        # testing in (while allowed out)
        graph = mutable_copy(i1.rdf_get())
        graph.add((ONS.foo, RNS.rw_out, i1.uri))
        with assert_raises(InvalidDataError):
            i1.rdf_put(graph)
        # testing out (while allowed in)
        graph = mutable_copy(i1.rdf_get())
        graph.add((i1.uri, RNS.rw_in, ONS.foo))
        with assert_raises(InvalidDataError):
            i1.rdf_put(graph)
    
    def test_putable_type(self):
        i1 = self.service.get(self.uri)
        graph = mutable_copy(i1.rdf_get())
        graph.add((i1.uri, RDF.type, RNS.rw_type))
        i1.rdf_put(graph)
        assert_same_graph(graph, i1.rdf_get())
        graph.remove((i1.uri, RDF.type, RNS.rw_type))
        i1.rdf_put(graph)
        assert_same_graph(graph, i1.rdf_get())
    
    def test_putable_in(self):
        i1 = self.service.get(self.uri)
        graph = mutable_copy(i1.rdf_get())
    
        if self.cls is Folder:
            # only try to change value,
            # as rw_in has cardinality constraints in Folder
            graph.remove((None, RNS.rw_in, i1.uri))
            graph.add((ONS.bar, RNS.rw_in, i1.uri))
            i1.rdf_put(graph)
            assert_same_graph(graph, i1.rdf_get())

        else:
            # try 0, 1 and 2 values
            graph.remove((None, RNS.rw_in, i1.uri))
            i1.rdf_put(graph)
            assert_same_graph(graph, i1.rdf_get())
    
            graph.add((ONS.foo, RNS.rw_in, i1.uri))
            i1.rdf_put(graph)
            assert_same_graph(graph, i1.rdf_get())
    
            graph.add((ONS.bar, RNS.rw_in, i1.uri))
            i1.rdf_put(graph)
            assert_same_graph(graph, i1.rdf_get())
    
    def test_putable_out(self):
        i1 = self.service.get(self.uri)
        graph = mutable_copy(i1.rdf_get())
    
        if self.cls is Folder:
            # only try to change value,
            # as rw_out has cardinality constraints in Folder
            graph.remove((i1.uri, RNS.rw_out, None))
            graph.add((i1.uri, RNS.rw_out, ONS.bar))
            i1.rdf_put(graph)
            assert_same_graph(graph, i1.rdf_get())
        else:
            # try 0, 1 and 2 values
            graph.remove((i1.uri, RNS.rw_out, None))
            i1.rdf_put(graph)
            assert_same_graph(graph, i1.rdf_get())
    
            graph.add((i1.uri, RNS.rw_out, ONS.foo))
            i1.rdf_put(graph)
            assert_same_graph(graph, i1.rdf_get())
    
            graph.add((i1.uri, RNS.rw_out, ONS.bar))
            i1.rdf_put(graph)
            assert_same_graph(graph, i1.rdf_get())
    
    def test_post_uri_in_use(self):
        root = self.service.root
        graph = self.cls.populate(self.uri, root.uri)
        with assert_raises(InvalidDataError):
            root.rdf_post(graph)

    def test_post_second_bnode(self):
        root = self.service.root
        graph = self.cls.populate(BNode(), root.uri)
        root.rdf_post(graph)


class TestWithOneItem(_TestWithOneElement):
    uri = ROOT.i1
    cls = Item

class TestWithOneFolder(_TestWithOneElement):
    uri = ROOT["f1/"]
    cls = Folder


def test_cardinality():
    for cls in ["Item", "Folder",]:
        for prop, cmin, cmax in [
            ("c1_in",   1, 1),
            ("c01_in",  0, 1),
            ("c23_in",  2, 3),
            ("c1n_in",  1, 999),
            ("c0_in",   0, 0),
            ("c1_out",  1, 1),
            ("c01_out", 0, 1),
            ("c23_out", 2, 3),
            ("c1n_out", 1, 999),
            ("c0_out",  0, 0),
            ]:
            for i in range(4):
                if cls == "Item":
                    # check that opposite direction is always allowed
                    # (but not in Folder, where ONS is reserved)
                    yield check_cardinality, cls, prop, i, "opposite"
                if cls == "Folder" and prop[:3] == "c01":
                    # c01_in and c01_out are not allowed on Folders
                    must_pass = (i == 0)
                else:                
                    must_pass = (cmin <= i <= cmax)
                yield check_cardinality, cls, prop, i, must_pass

    # cardinality constraints overridden in Folder
    for prop, cmin, cmax in [
        ("rw_in",  1, 1),
        ("rw_out", 1, 1),
        ]:
        for i in range(4):
            must_pass = (cmin <= i <= cmax)
            yield check_cardinality, "Folder", prop, i, must_pass

def check_cardinality(cls, prop, num, must_pass):
    # pre-process arguments
    cls = globals()[cls]
    if prop[0] == "r":
        prop = RNS[prop]
    else:
        prop = ONS[prop]
    if prop[-3:] == "_in":
        direction = -1
    else:
        direction = 1
    if must_pass == "opposite":
        # testing that direction opposite to the constraint always pass
        direction = -direction
        must_pass = True
    direction = slice(None, None, direction)

    # setUp service
    service = MyService()
    graph = cls.populate(BNode, service.root.uri)
    uri = service.root.rdf_post(graph)[0]
    created = service.get(uri)
    # alter graph with 'num' occurences of 'prop'
    graph.remove((uri, prop, None)[direction])
    for i in range(num):
        other = ONS["other%s" % i]
        graph.add((uri, prop, other)[direction])
    # do test
    if must_pass:
        created.rdf_put(graph)
    else:
        with assert_raises(InvalidDataError):
            created.rdf_put(graph)


def test_bk():
    service = MyService()
    root = service.root
    assert hasattr(root, "etag")
    assert hasattr(root, "last_modified")

def test_bk_changed_on_put():
    service = MyService()
    root = service.root
    old_etag = root.etag
    old_lm = root.last_modified
    graph = mutable_copy(root.rdf_get())
    graph.add((root.uri, RDFS.label, Literal("modified")))
    sleep(0.05) # ensures last_modified will actually change
    root.rdf_put(graph)
    assert root.etag != old_etag
    assert root.last_modified > old_lm

def test_bk_changed_on_post():
    service = MyService()
    root = service.root
    old_etag = root.etag
    old_lm = root.last_modified
    root.rdf_post(Item.populate(BNode(), root.uri))
    assert root.etag != old_etag
    assert root.last_modified > old_lm
    

# toolbox                      

def assert_same_graph(g1, g2):
    in_both, in_first, in_second = graph_diff(g1, g2)
    def dump_diff():
        return "\n+++\n%s---\n%s===\n" % (
            in_first.serialize(format="n3"),
            in_second.serialize(format="n3"),
            )
    assert len(in_both) == len(g1), dump_diff()
    assert len(in_first) == 0, dump_diff()
    assert len(in_first) == 0, dump_diff()

def mutable_copy(graph):
    ret = Graph()
    for triple in graph:
        ret.add((triple))
    return ret
