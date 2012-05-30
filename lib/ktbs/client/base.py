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

from ktbs.client.resource import register, Resource
from ktbs.common.base import BaseMixin
from ktbs.common.utils import post_graph
from ktbs.namespaces import KTBS
from rdfrest.utils import coerce_to_node, coerce_to_uri, random_token

class Base(BaseMixin, Resource):
    """I implement a client proxy on the root of a kTBS.
    """

    RDF_MAIN_TYPE = KTBS.Base

    def create_model(self, parents=None, id=None, graph=None):
        """Create a new model in this trace base.

        :param parents: either None, or an iterable of models from which this
                        model inherits
        :param id: see :ref:`ktbs-resource-creation`
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.client.model.Model`
        """
        #pylint: disable-msg=W0622
        #    redefining built-in 'id'
        node = coerce_to_node(id, self.uri)
        if graph is None:
            graph = Graph()
        graph.add((node, _RDF_TYPE, _TRACE_MODEL))
        graph.add((self.uri, _CONTAINS, node))

        uri = self.uri
        add = graph.add
        for parent in parents or ():
            parent = coerce_to_uri(parent, uri)
            add((node, _HAS_PARENT_MODEL, parent))

        rheaders, _rcontent = post_graph(graph, self.uri)
        created_uri = rheaders['location']
        return self.factory(created_uri, _TRACE_MODEL)


    def create_stored_trace(self, model, origin=None, default_subject=None,
                            id=None, graph=None):
        """Create a new store trace in this trace base.

        :param model: Trace associated model
        :param origin: Typically a timestamp. It can be an opaque string, 
             meaning that the precise time when the trace was collected is not
             known
        :param default_subject: The subject to set to new obsels when they do
            not specifify a subject
        :param id: see :ref:`ktbs-resource-creation`
        :param graph: see :ref:`ktbs-resource-creation`
        """
        # redefining built-in 'id' #pylint: disable=W0622
        node = coerce_to_node(id, self.uri)

        if graph is None:
            graph = Graph()
        graph.add((node, _RDF_TYPE, _STORED_TRACE))
        graph.add((self.uri, _CONTAINS, node))

        model_uri = coerce_to_uri(model, self.uri)
        graph.add((node, _HAS_MODEL, model_uri))

        if origin is None:
            origin = random_token(32)
        elif isinstance(origin, int):
            origin = datetime.fromtimestamp(origin)
        graph.add((node, _HAS_ORIGIN, Literal(origin)))

        if default_subject is not None:
            graph.add((node, _HAS_DEFAULT_SUBBJECT, Literal(default_subject)))

        rheaders, _rcontent = post_graph(graph, self.uri)
        created_uri = rheaders['location']
        return self.factory(created_uri, _STORED_TRACE)

    # TODO implement other create_X


register(Base)

# the following import ensures that required classes are registered as well
# (Model, StoredTrace, ComputedTrace, Method)
#import ktbs.client.method #pylint: disable-msg=W0611
import ktbs.client.model #pylint: disable-msg=W0611
import ktbs.client.trace #pylint: disable-msg=W0611,W0404
# NB: we have to disable pylint W0611 (Unused import) and W0404 (Reimport)


_CONTAINS = KTBS.contains
_HAS_DEFAULT_SUBBJECT = KTBS.hasDefaultSubject
_HAS_PARENT_MODEL = KTBS.hasParentModel
_TRACE_MODEL = KTBS.TraceModel
_RDF_TYPE = RDF.type
_STORED_TRACE = KTBS.StoredTrace
_COMPUTED_TRACE = KTBS.ComputedTrace
_HAS_MODEL = KTBS.hasModel
_HAS_ORIGIN = KTBS.hasOrigin
