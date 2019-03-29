"""
This plugins defines the VirtuosoS RDFlib store,
to use Virtuoso as a triple-store for kTBS through its SPARQL-update endpoint.

The configuration string is a '|' separated list containing:
- the URL authenticated endpoint
- the admin username
- the admin password

Exemple configuration::

   [rdf_database]
   repository = :VirtuosoS:http://localhost:8890/sparql-auth|dba|dba

   [plugins]
   virtuoso_sparql = true

IMPORTANT:

* you must install dependencies with ``pip install -r requirements.d/virtuoso_sparql.txt``
* it is recommended to increase the maximum number of rows that Virtuoso can return for a SPARQL query:
  ``Virtuoso Conductor > System Admin > Parameters > SPARQL > ResultSetMaxRows``
"""
# see https://gist.github.com/pchampin/ab3d01d2c3c245042dc5

from itertools import islice
import re
from uuid import uuid4

from rdflib import BNode, URIRef
from rdflib.plugins.sparql.sparql import FrozenBindings
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore, _node_to_sparql, _node_from_result, SPARQL_NS

from SPARQLWrapper.SmartWrapper import SPARQLWrapper2

def _virtuoso_compatible_generator():
    return unicode(uuid4().int % 2**61)

def _virtuoso_node_to_sparql(node):
    if isinstance(node, BNode):
        return '<nodeID://{}>'.format(node)
    else:
        return node.n3()

def _virtuoso_node_from_result(element):
    if element.tag == '{%s}bnode' % SPARQL_NS:
        return BNode(element.text[9:])
    else:
        return _node_from_result(element)


_BASE_RE = re.compile(r'(BASE[ \t]+<[^>]*>\s+)?', re.IGNORECASE + re.MULTILINE)

class VSPARQLStore(SPARQLUpdateStore):
    opened = False

    def __init__(self, config_or_endpoint=None, username=None, password=None, **kwargs):
        if config_or_endpoint is not None:
            if username is not None:
                assert password is not None
                self._do_init(config_or_endpoint, username, password, **kwargs)
            else:
                self.open(config_or_endpoint)

    def open(self, configuration, create=False):
        assert not self.opened, "Store already open"
        endpoint, username, password = configuration.split('|')
        self._do_init(endpoint, username, password)
    
    def _do_init(self, endpoint, username, password, **kwargs):
        SPARQLUpdateStore.__init__(self, endpoint, endpoint,
                                   node_to_sparql=_virtuoso_node_to_sparql,
                                   node_from_result=_virtuoso_node_from_result,
                                   **kwargs)
        self.setHTTPAuth('digest')
        self.setCredentials(username, password)
        self.setReturnFormat = "json"
        self.opened = True

    
    def injectPrefixes(self, query):
        """
        Better implentation than NSSPARQLWrapper.injectPrefixes,
        as it injects prefixes *after* the BASE clause if any
        """
        parts = []
        match_base = _BASE_RE.search(query)
        if match_base:
            parts.append(query[:match_base.end()])
            query = query[match_base.end():]

        prefixes = list(self.nsBindings.items())
        parts.extend('PREFIX %s: <%s>' % (k, v) for k, v in prefixes)
        parts.extend([
            '', # separate prefixes from query with an empty line
            query,
        ])
        return '\n'.join(parts)

    def query(self, query, initNs, initBindings, queryGraph, **kwargs):
        prepared_base = None
        if hasattr(query, '_original_args'):
            query, prepared_ns, prepared_base = query._original_args
            if not initNs:
                initNs = prepared_ns
            else:
                prepared_ns = dict(prepared_ns)
                prepared_ns.update(initNs)
                initNs = prepared_ns

        base = kwargs.pop("base", None) or prepared_base
        if base is not None:
            query = '\n'.join([('BASE <%s>' % base), query])

        res = SPARQLUpdateStore.query(self, query, initNs, initBindings, queryGraph, **kwargs)
        if res.bindings is not None:
            res.bindings = ( FrozenBindings(None, i) for i in res.bindings )

        return res

    def __addN(self, quads):
        for batch in ibatch(quads, 100):
            SPARQLUpdateStore.addN(self, quads)

def ibatch(iterator, n):
    """
    Split an iterator into batches of n elements max.
    """
    while True:
        batch = list(islice(iterator, n))
        if batch:
            yield batch
        else:
            break

def monkeypatch_prepare_query():
    """
    ensures that rdflib.plugins.sparql.processor is uptodate, else monkeypatch it.
    """
    # pylint: disable=invalid-name
    import rdflib.plugins.sparql.processor as sparql_processor
    _TEST_PREPARED_QUERY = sparql_processor.prepareQuery("ASK { ?s ?p ?o }")
    if not hasattr(_TEST_PREPARED_QUERY, "_original_args"):
        # monkey-patch 'prepare'
        original_prepareQuery = sparql_processor.prepareQuery
        def monkeypatched_prepareQuery(queryString, initNS=None, base=None):
            """
            A monkey-patched version of the original prepareQuery,
            adding an attribute '_original_args' to the result.
            """
            if initNS is None:
                initNS = {}
            ret = original_prepareQuery(queryString, initNS, base)
            ret._original_args = (queryString, initNS, base)
            return ret
        sparql_processor.prepareQuery = monkeypatched_prepareQuery
        log.info("monkey-patched rdflib.plugins.sparql.processor.prepareQuery")


def start_plugin(config):
    #pylint: disable=W0603
    import rdflib.plugin
    import rdflib.store

    # monkey patch BNode to make it virtuoso compatible
    monkeypatch_prepare_query()
    BNode.__new__.func_defaults = (None, _virtuoso_compatible_generator, 'b')

    rdflib.plugin.register("VirtuosoS", rdflib.store.Store,
        "ktbs.plugins.virtuoso_sparql", "VSPARQLStore")

def stop_plugin():
    pass

if __name__ == "__main__":
    from rdflib import Namespace, Graph, Literal
    from rdflib.collection import Collection

    start_plugin(None)

    EX = Namespace('http://example.org/')
    #store = VSPARQLStore('http://localhost:8890/sparql-auth', 'dba', 'dba')
    g = Graph("VirtuosoS", EX.g)
    g.open("http://localhost:8890/sparql-auth|dba|dba")
    g.remove((None, None, None))
    assert len(g) == 0

    bn = BNode()
    g.add((EX.s, EX.p1, bn))
    g.add((bn, EX.p2, Literal("foo")))
    assert len(g) == 2

    lh = BNode()
    g.add((EX.s, EX.p3, lh))
    lst = Collection(g, lh, map(Literal, [1,2,3]))
    assert len(g) == 9

    print(g.serialize(format="turtle"))
    
    g.remove((None, None, None))


