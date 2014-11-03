# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
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
I provide the pythonic interface of ktbs:Base .
"""

from rdflib import Graph, Literal, RDF, URIRef

from rdfrest.exceptions import InvalidDataError
from rdfrest.util import coerce_to_node, coerce_to_uri, parent_uri
from rdfrest.wrappers import register_wrapper
from .resource import KtbsResourceMixin
from ..namespace import KTBS
from ..utils import extend_api, SKOS


@register_wrapper(KTBS.Base)
@extend_api
class BaseMixin(KtbsResourceMixin):
    """
    I provide the pythonic interface common to bases.
    """

    def __iter__(self):
        self_factory = self.factory
        for uri, typ in self._iter_contained():
            yield self_factory(uri, typ)

    ######## Abstract kTBS API ########

    def iter_traces(self):
        """
        Iter over all the traces (stored or computed) of this base.
        """
        self_factory = self.factory
        for uri, typ in self._iter_contained():
            if typ == KTBS.StoredTrace or typ == KTBS.ComputedTrace:
                yield self_factory(uri, typ)

    def iter_models(self):
        """
        Iter over all the trace models of this base.
        """
        self_factory = self.factory
        for uri, typ in self._iter_contained():
            if typ == KTBS.TraceModel:
                yield self_factory(uri, typ)

    def iter_methods(self):
        """
        Iter over all the methods of this base.
        """
        self_factory = self.factory
        for uri, typ in self._iter_contained():
            if typ == KTBS.Method:
                yield self_factory(uri, typ)

    def get(self, id):
        """
        Return one of the element contained in the base.

        :param id: the URI of the element; can be relative to the URI of the
                   base
        :type  id: str

        :rtype: `~.trace_model.TraceModelMixin`:class:,
                `~.method.Method`:class: or `~.trace.AbstractTraceMixin`:class:
        """
        #  Redefining built-in id #pylint: disable-msg=W0622
        elt_uri = coerce_to_uri(id, self.uri)
        ret = self.factory(elt_uri)
        assert ret is None  or  isinstance(ret, InBaseMixin)
        return ret

    def get_root(self):
        """
        Return the root of the KTBS containing this base.
        """
        root_uri = URIRef("..", self.uri)
        return self.factory(root_uri, KTBS.KtbsRoot)
        # assert must be .ktbs_root.KtbsRootMixin

    def create_model(self, id=None, parents=None, label=None, graph=None):
        """Create a new model in this trace base.

        :param id: see :ref:`ktbs-resource-creation`
        :param parents: either None, or an iterable of models from which this
                        model inherits
        :param label: explain.
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.client.model.Model`
        """
        # redefining built-in 'id' #pylint: disable-msg=W0622

        trust = graph is None  and  id is None
        node = coerce_to_node(id, self.uri)
        if parents is None:
            parents = () # abstract API allows None
        if graph is None:
            graph = Graph()
        graph.add((self.uri, KTBS.contains, node))
        graph.add((node, RDF.type, KTBS.TraceModel))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))
        for parent in parents:
            parent = coerce_to_uri(parent, self.uri)
            graph.add((node, KTBS.hasParentModel, parent))
        uris = self.post_graph(graph, None, trust, node, KTBS.TraceModel)
        assert len(uris) == 1
        return self.factory(uris[0], KTBS.TraceModel)
        # must be a .trace_model.TraceModelMixin

    def create_method(self, id=None, parent=None, parameters=None, label=None,
                      graph=None):
        """Create a new computed trace in this trace base.

        :param id: see :ref:`ktbs-resource-creation`
        :param parent: parent method (required)
        :param parameters: method parameters
        :param label: explain.
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.client.method.Method`
        """
        # redefining built-in 'id' #pylint: disable-msg=W0622

        # We somehow duplicate Method.check_new_graph here, but this is
        # required if we want to be able to set _trust=True below.
        # Furthermore, the signature of this method makes it significantly
        # easier to produce a valid graph, so there is a benefit to this
        # duplication.
            
        if parent is None:
            raise ValueError("parent is mandatory")
        trust = graph is None  and  id is None
        node = coerce_to_node(id, self.uri)
        parent = coerce_to_uri(parent, self.uri)
        if parameters is None:
            parameters = {}

        if trust:
            if parent.startswith(self.uri):
                if not (parent, RDF.type, KTBS.Method) in self.state:
                    raise InvalidDataError("Parent <%s> is not a Method"
                                           % parent)
            else:
                trust = False # could be built-in, let impl/server check
        if graph is None:
            graph = Graph()
        graph.add((self.uri, KTBS.contains, node))
        graph.add((node, RDF.type, KTBS.Method))
        graph.add((node, KTBS.hasParentMethod, parent))
        for key, value in parameters.iteritems():
            if "=" in key:
                raise ValueError("Parameter name can not contain '=': %s", key)
            graph.add((node, KTBS.hasParameter,
                       Literal(u"%s=%s" % (key, value))))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))
        uris = self.post_graph(graph, None, trust, node, KTBS.Method)
        assert len(uris) == 1
        return self.factory(uris[0], KTBS.Method)
        # must be a .method.MethodMixin


    def create_stored_trace(self, id=None, model=None, origin=None, 
                            default_subject=None, label=None, graph=None):
        """Create a new store trace in this trace base.

        :param id: see :ref:`ktbs-resource-creation`
        :param model: mode of the trace to create (required)
        :param origin: Typically a timestamp. It can be an opaque string, 
             meaning that the precise time when the trace was collected is not
             known
        :param default_subject: The subject to set to new obsels when they do
            not specifify a subject
        :param label: explain.
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.client.trace.StoredTrace`
        """
        # redefining built-in 'id' #pylint: disable=W0622

        # We somehow duplicate StoredTrace.complete_new_graph and
        # StoredTrace.check_new_graph here, but this is required if we want to
        # be able to set _trust=True below.
        # Furthermore, the signature of this method makes it significantly
        # easier to produce a valid graph, so there is a benefit to this
        # duplication.

        if model is None:
            raise ValueError("model is mandatory")
        trust = graph is None  and  id is None
        node = coerce_to_node(id, self.uri)
        model = coerce_to_uri(model, self.uri)
        origin_isoformat = getattr(origin, "isoformat", None)
        if origin_isoformat:
            origin = origin_isoformat()

        if graph is None:
            graph = Graph()
        graph.add((self.uri, KTBS.contains, node))
        graph.add((node, RDF.type, KTBS.StoredTrace))
        graph.add((node, KTBS.hasModel, model))
        graph.add((node, KTBS.hasOrigin, Literal(origin)))
        if default_subject is not None:
            graph.add((node, KTBS.hasDefaultSubject, Literal(default_subject)))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))

        uris = self.post_graph(graph, None, trust, node, KTBS.StoredTrace)
        assert len(uris) == 1
        return self.factory(uris[0], KTBS.StoredTrace)
        # must be a .trace.StoredTraceMixin

    def create_computed_trace(self, id=None, method=None, parameters=None,
                              sources=None, label=None, graph=None):
        """Create a new computed trace in this trace base.

        :param id: see :ref:`ktbs-resource-creation`
        :param method: method to apply for computation (required)
        :param parameters: parameters of the method
        :param sources: source traces to which the method is applied
        :param label: explain.
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.client.trace.ComputedTrace`
        """
        # redefining built-in 'id' #pylint: disable=W0622

        # We somehow duplicate ComputedTrace.complete_new_graph and
        # ComputedTrace.check_new_graph here, but this is required if we want to
        # be able to set _trust=True below.
        # Furthermore, the signature of this method makes it significantly
        # easier to produce a valid graph, so there is a benefit to this
        # duplication.
            
        if method is None:
            raise ValueError("method is mandatory")
        trust = graph is None  and  id is None
        node = coerce_to_node(id, self.uri)
        method = coerce_to_uri(method, self.uri)
        if sources is None:
            sources = ()
        else:
            sources = [ coerce_to_uri(i, self.uri) for i in sources ]
        if parameters is None:
            parameters = {}
        
        if trust:
            # we need to check some integrity constrains,
            # because the graph may be blindly trusted
            if method.startswith(self.uri):
                if not (method, RDF.type, KTBS.Method) in self.state:
                    raise InvalidDataError("<%s> is not a Method" % method)
            else:
                trust = False # could be built-in, let impl/server check
            for src in sources:
                if self.state.value(src, RDF.type) not in (KTBS.StoredTrace,
                                                           KTBS.ComputedTrace):
                    raise ValueError("Source <%s> is not a trace of this base"
                                     % src)
        if graph is None:
            graph = Graph()
        graph.add((self.uri, KTBS.contains, node))
        graph.add((node, RDF.type, KTBS.ComputedTrace))
        graph.add((node, KTBS.hasMethod, method))
        for src in sources:
            graph.add((node, KTBS.hasSource, src))
        for key, value in parameters.iteritems():
            if "=" in key:
                raise ValueError("Parameter name can not contain '=': %s", key)
            graph.add((node, KTBS.hasParameter,
                       Literal(u"%s=%s" % (key, value))))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))

        uris = self.post_graph(graph, None, trust, node, KTBS.ComputedTrace)
        assert len(uris) == 1
        return self.factory(uris[0], KTBS.ComputedTrace)
        # must be a .trace.StoredTraceMixin

    def remove(self):
        """Delete this base from the kTBS.
        """
        root = self.get_root()
        super(BaseMixin, self).remove()
        root.force_state_refresh()

    ######## Private methods ########

    def _iter_contained(self):
        """
        Yield the URI and type of every element of this base.
        """
        query_template = """
            PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>
            SELECT DISTINCT ?s ?t
            WHERE { <%s> k:contains ?s . ?s a ?t . }
        """
        return iter(self.state.query(query_template % self.uri))
            


@extend_api
class InBaseMixin(KtbsResourceMixin):
    """
    Common mixin for all elements of a trace base.
    """
    #pylint: disable-msg=R0903
    # Too few public methods

    ######## Abstract kTBS API ########

    def get_base(self):
        """
        Return the trace base this element belongs to.

        :rtype: `BaseMixin`:class:
        """
        base_uri = parent_uri(self.uri)
        ret = self.factory(base_uri, KTBS.Base)
        assert isinstance(ret, BaseMixin)
        return ret

    def remove(self):
        """Delete this element from its base.
        """
        base = self.get_base()
        super(InBaseMixin, self).remove()
        base.force_state_refresh()
