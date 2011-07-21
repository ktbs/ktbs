#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
I provide the client implementation of a trace Base.
"""
from rdflib import Graph, RDF, Literal
#from rdfrest.client import ProxyStore

from datetime import datetime

from ktbs.client.resource import Resource, RESOURCE_MAKER
from ktbs.common.base import BaseMixin
from ktbs.common.utils import coerce_to_node, coerce_to_uri, post_graph
from ktbs.namespaces import KTBS

class Base(BaseMixin, Resource):
    """I implement a client proxy on the root of a kTBS.
    """

    def create_model(self, parents=None, id=None, graph=None):
        """Create a new model in this trace base.
        :param parents: either None, one or several models this model inherits 
        from
        :param id: either None, a relative URI or a BNode present in graph
        :param graph: if not none, may contain additional properties for ???
        """
        #pylint: disable-msg=W0622
        #    redefining built-in 'id'
        self_uri = self.uri
        node = coerce_to_node(id, self_uri)
        if graph is None:
            graph = Graph()
        graph.add((node, _RDF_TYPE, _TRACE_MODEL))
        graph.add((self.uri, _CONTAINS, node))

        uri = self_uri
        add = graph.add
        for parent in parents or ():
            parent = coerce_to_uri(parent, uri)
            add((node, _HAS_PARENT_MODEL, parent))

        rheaders, _rcontent = post_graph(graph, self.uri)
        created_uri = rheaders['location']
        # TODO MAJOR parse content and feed the graph to make_resource
        return self.make_resource(created_uri, _TRACE_MODEL)


    def create_stored_trace(self, model=None, origin=None, 
                            default_subject=None, id=None, graph=None):
        """Create a new store trace in this trace base.
        :param model: Trace associated model
        :param origin: Typically a timestamp. It can be an opaque string, 
        meaning that the precise time when the trace was collected is not known
        :param default_subject: ???
        :param id: either None ? a relative URI or a BNode present in graph
        :param graph: if not none, may contain additional properties for ???
        """
        #pylint: disable-msg=W0622
        #    redefining built-in 'id'
        self_uri = self.uri
        node = coerce_to_node(id, self_uri)

        if model is None:
            raise ValueError("You must supply a model for the %s trace."
                             % id) 

        if graph is None:
            graph = Graph()
        graph.add((node, _RDF_TYPE, _STORED_TRACE))
        graph.add((self.uri, _CONTAINS, node))

        model_uri = coerce_to_uri(model, self_uri)
        graph.add((node, _HAS_MODEL, model_uri))

        if origin is not None:
            graph.add((node, _HAS_ORIGIN, origin))
        else:
            # TODO what do we use as defaut value ?
            graph.add((node, _HAS_ORIGIN, Literal(str(datetime.now()))))

        rheaders, _rcontent = post_graph(graph, self.uri)
        created_uri = rheaders['location']
        # TODO MAJOR parse content and feed the graph to make_resource ???
        return self.make_resource(created_uri, _COMPUTED_TRACE)

    # TODO implement other create_X


RESOURCE_MAKER[KTBS.Base] = Base

_CONTAINS = KTBS.contains
_HAS_PARENT_MODEL = KTBS.hasParentModel
_TRACE_MODEL = KTBS.TraceModel
_RDF_TYPE = RDF.type
_STORED_TRACE = KTBS.StoredTrace
_COMPUTED_TRACE = KTBS.ComputedTrace
_HAS_MODEL = KTBS.hasModel
_HAS_ORIGIN = KTBS.hasOrigin

# the following import ensures that required classes are registered in
# RESOURCE_MAKER (Model, StoredTrace, ComputedTrace, Method)
#import ktbs.client.method #pylint: disable-msg=W0611
import ktbs.client.model #pylint: disable-msg=W0611
import ktbs.client.trace #pylint: disable-msg=W0611,W0404
# NB: we have to disable pylint W0611 (Unused import) and W0404 (Reimport)
