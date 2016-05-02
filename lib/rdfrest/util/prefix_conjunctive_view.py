# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011 Françoise Conil <francoise.conil@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    RDF-REST is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RDF-REST is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with RDF-REST.  If not, see <http://www.gnu.org/licenses/>.

"""
I implement PrefixConjunctiveView,
a read-only ConjunctiveGraph exposing only a subset of the store,
defined by a prefix URI for all named graphs.
"""

from itertools import chain
import logging
from rdflib import ConjunctiveGraph, Graph, Literal
from rdflib.paths import Path
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.sparql import Query
from re import compile as Regexp, IGNORECASE, escape as regex_escape

LOG = logging.getLogger(__name__)

class PrefixConjunctiveView(ConjunctiveGraph):

    """
    A read-only dataset exposing a subset of the underlying store.

    More precisely,
    only a subset of the named graph in the store are included.

    The default graph is the union of all included named graphs.
    The `contexts` method iter only over the included named graphs.
    """

    def __init__(self, prefix, store='default', identifier=None):
        self._in_init = True
        super(PrefixConjunctiveView, self).__init__(store, identifier=identifier)
        del self._in_init

        assert self.store.context_aware, ("ConjunctiveGraph must be backed by"
                                          " a context aware store.")
        self.context_aware = True
        self._prefix = prefix
        self._include = lambda uri: uri.startswith(prefix)
        self._whole = ConjunctiveGraph(store)
        self._filter = u"FILTER STRSTARTS(STR(?g)," + Literal(prefix).n3() + u")"
        #self._filter = u'FILTER REGEX(str(?g), "^' + prefix + u'")' # faster in Virtuoso, but unsafe (the URI may contain special characters
        self._sparql_declaration = None

        self._store_can_query = False
        if hasattr(store, 'query'):
            try:
                store.query('# TODO some query to check that the store supports a clever optimization')
                # IDEA: may be use FROM/FROM NAMED (self.sparal_declaration) if the number of graphs is low enough?
                self._store_can_query = True
            except:
                pass

    @property
    def default_union(self):
        """
        PrefixConjunctiveView.default_union is always True.
        """
        return True
    @default_union.setter
    def default_union(self, value):
        """
        Ignore changes of default_union.
        """
        if getattr(self, '_in_init', None):
            pass
        else:
            raise TypeError(
                'PrefixConjunctiveView.default_union is read-only')

    @property
    def sparql_declaration(self):
        """
        The sparql FROM and FROM NAMED clauses defining this partial dataset.
        """
        if self._sparql_declaration is None:
            n3s = None # TODO build list by inspecting store
            dataset = ( [' FROM', i, ' FROM NAMED', i] for i in n3s )
            self._sparql_declaration = ''.join(chain(*dataset))

        return self._sparql_declaration

    def __str__(self):
        pattern = ("[a rdflib:PrefixConjunctiveView;rdflib:storage "
                   "[a rdflib:Store;rdfs:label '%s']]")
        return pattern % self.store.__class__.__name__

    def __reduce__(self):
        return (ConjunctiveGraph, (self._prefix, self.store, self.identifier))

    def __len__(self):
        """Number of triples in the entire conjunctive graph"""
        return int(
            self._whole.query(u'SELECT (COUNT(?s) as ?c)'
                              u'{GRAPH ?g {?s ?p ?o } %s}' % self._filter)
            .bindings[0]['c']
        )

    def __contains__(self, triple_or_quad):
        """Support for 'triple/quad in graph' syntax"""
        for _ in self.triples(triple_or_quad):
            return True
        return False


    def _spoc(self, triple_or_quad, context=None):
        """
        helper method for having methods that support
        either triples or quads
        """
        if triple_or_quad is None:
            triple_or_quad = (None, None, None)
        if len(triple_or_quad) == 3:
            s, p, o = triple_or_quad
            if context is not None:
                c = context.identifier
            else:
                c = None
        elif len(triple_or_quad) == 4:
            s, p, o, c = triple_or_quad
            if context is not None:
                c = context.identifier
        if c is not None and not self._include(c):
            c = _FAIL
        return s,p,o,c

    def contexts(self, triple=None):
        """Iterate over all contexts in the graph

        If triple is specified, iterate over all contexts the triple is in.
        """
        initBindings = {}
        if triple:
            initBindings['s'], initBindings['p'], initBindings['o'] = triple

        store = self.store
        for gid, in self._whole.query(u'SELECT DISTINCT ?g'
                                      u'{GRAPH ?g { ?s ?p ?o } %s}'
                                      % self._filter,
                                      initBindings=initBindings):
            yield Graph(store, gid, self)

    def get_context(self, identifier, quoted=False):
        """Return a context graph for the given identifier

        identifier must be a URIRef or BNode.
        """
        assert not quoted, \
            'PrefixConjunctiveView does not support quoted graphs'
        if self._include(identifier):
            return Graph(self.store, identifier, self)
        else:
            return None


    def triples(self, triple_or_quad, context=None):
        """
        Iterate over all the triples in the entire conjunctive graph

        For legacy reasons, this can take the context to query either
        as a fourth element of the quad, or as the explicit context
        keyword paramater. The kw param takes precedence.
        """

        s,p,o,c = self._spoc(triple_or_quad, context)
        if c is _FAIL:
            return []

        if isinstance(p, Path):
            if c is None:
                ctx = self
            else:
                ctx = Graph(self.store, c, self)
            return ((s, p, o) for s, o in p.eval(ctx, s, o))

        else:
            initBindings = {}
            if s is not None:
                initBindings['s'] = s
            if p is not None:
                initBindings['p'] = p
            if o is not None:
                initBindings['o'] = o
            if c is not None:
                initBindings['g'] = c
                filter_clause = ""
            else:
                filter_clause = self._filter
            return self._whole.query(u'SELECT ?s ?p ?o'
                                     u'{ GRAPH ?g { ?s ?p ?o } %s}'
                                     % filter_clause,
                                     initBindings=initBindings)

    def quads(self, triple_or_quad=None):
        """Iterate over all the quads in the entire conjunctive graph"""

        s,p,o,c = self._spoc(triple_or_quad)
        if c is _FAIL:
            return

        initBindings = {}
        graph_cache = {}
        store = self.store
        if s is not None:
            initBindings['s'] = s
        if p is not None:
            initBindings['p'] = p
        if o is not None:
            initBindings['o'] = o
        if c is not None:
            initBindings['g'] = c
            graph_cache[c] = Graph(store, c, self)
            filter_clause = ""
        else:
            filter_clause = self._filter

        for s, p, o, g in self._whole.query(u'SELECT ?s ?p ?o ?g'
                                            u'{ GRAPH ?g { ?s ?p ?o } %s}'
                                            % filter_clause,
                                            initBindings=initBindings):
            ctx = graph_cache.get(g)
            if ctx is None:
                ctx = graph_cache[g] = Graph(store, g, self)
            yield s, p, o, ctx

    def triples_choices(self, (s, p, o), context=None):
        """Iterate over all the triples in the entire conjunctive graph"""
        raise NotImplemented

    def query(self, query_object, processor='sparql',
              result='sparql', initNs=None, initBindings=None,
              use_store_provided=True, **kwargs):
        """
        Query this graph.

        A type of 'prepared queries' can be realised by providing
        initial variable bindings with initBindings

        Initial namespaces are used to resolve prefixes used in the query,
        if none are given, the namespaces from the graph's namespace manager
        are used.

        :returntype: rdflib.query.QueryResult
        """
        if isinstance(query_object, Query):
            sparql, initNS, _ = query_object._original_args
            algebra = query_object.algebra
        else:
            sparql = query_object
            algebra = parseQuery(query_object)
        if algebra[1].datasetClause:
            raise ValueError('PrefixConjunctiveView does not support '
                             'FROM or FROM NAMED clauses in SPARQL')

        if use_store_provided and self._store_can_query:
            # not actually used for the moment
            # (_store_can_query is always False)
            # below is a tentative implementation,
            # but it will not scale if the number of included graphs is too high.
            if algebra[1].name == ('ConstructQuery'):
                cend = CONSTRUCT.search(sparql).end()
                wspan = WHERE.search(sparql[cend:]).span()
                prefix = sparql[:cend+wspan[0]]
                suffix = sparql[cend+wspan[1]:]
            else:
                prefix, _, suffix = WHERE.split(sparql, 1)
            processed_sparql = ''.join([
                prefix, self.sparql_declaration, '{', suffix
            ])
            return self.store.query(
                processed_sparql,
                initNs or dict(self.namespaces()),
                initBindings or {},
                '__UNION__',
                **kwargs)
        else:
            return super(PrefixConjunctiveView, self).query(
                query_object, processor, result, initNs, initBindings, False, **kwargs
            )


    def add(self, triple_or_quad):
        """
        Add a triple or quad to the store.

        if a triple is given it is added to the default context
        """
        raise TypeError('PrefixConjunctiveView is read-only')

    def addN(self, quads):
        """Add a sequence of triples with context"""
        raise TypeError('PrefixConjunctiveView is read-only')

    def remove(self, triple_or_quad):
        """
        Removes a triple or quads

        if a triple is given it is removed from all contexts

        a quad is removed from the given context only
        """
        raise TypeError('PrefixConjunctiveView is read-only')

    def remove_context(self, context):
        """Removes the given context from the graph"""
        raise TypeError('PrefixConjunctiveView is read-only')

    def parse(self, source=None, publicID=None, format="xml",
              location=None, file=None, data=None, **args):
        """
        Parse source adding the resulting triples to its own context
        (sub graph of this graph).

        See :meth:`rdflib.graph.Graph.parse` for documentation on arguments.

        :Returns:

        The graph into which the source was parsed. In the case of n3
        it returns the root context.
        """
        raise TypeError('PrefixConjunctiveView is read-only')

CONSTRUCT = Regexp('construct *{', IGNORECASE)
WHERE = Regexp('(where)? *{', IGNORECASE)

_FAIL = "Graph is not included in this PrefixConjunctiveView"
