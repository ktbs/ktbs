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
from rdflib import Graph, RDF
#from rdfrest.client import ProxyStore

from ktbs.client.resource import Resource, RESOURCE_MAKER
from ktbs.common.base import BaseMixin
from ktbs.common.utils import coerce_to_node, coerce_to_uri, post_graph
from ktbs.namespaces import KTBS

class Base(BaseMixin, Resource):
    """I implement a client proxy on the root of a kTBS.
    """

    def create_model(self, parents=None, id=None, graph=None):
        """Create a new model in this trace base.
        id: either None, a relative URI or a BNode present in graph
        graph: if not none, may contain additional properties for the new base
        """
        #pylint: disable-msg=W0622
        #    redefining built-in 'id'
        self_uri = self.uri
        node = coerce_to_node(id, self_uri)
        if graph is None:
            graph = Graph()
        graph.add((node, _RDF_TYPE, _MODEL))
        graph.add((self.uri, _CONTAINS, node))

        uri = self_uri
        add = graph.add
        for parent in parents or ():
            parent = coerce_to_uri(parent, uri)
            add((node, _HAS_PARENT_MODEL, parent))

        rheaders, _rcontent = post_graph(graph, self.uri)
        created_uri = rheaders['location']
        # TODO MAJOR parse content and feed the graph to make_resource
        return self.make_resource(created_uri, _MODEL)

    # TODO implement other create_X


RESOURCE_MAKER[KTBS.Base] = Base

_CONTAINS = KTBS.contains
_HAS_PARENT_MODEL = KTBS.hasParentModel
_MODEL = KTBS.Model
_RDF_TYPE = RDF.type

# the following import ensures that required classes are registered in
# RESOURCE_MAKER (Model, StoredTrace, ComputedTrace, Method)
#import ktbs.client.method #pylint: disable-msg=W0611
import ktbs.client.model #pylint: disable-msg=W0611
import ktbs.client.trace #pylint: disable-msg=W0611,W0404
# NB: we have to disable pylint W0611 (Unused import) and W0404 (Reimport)
