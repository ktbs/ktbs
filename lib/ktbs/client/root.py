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
I provide the client implementation of KtbsRoot.
"""
from rdflib import Graph, Literal, RDF
#from rdfrest.client import ProxyStore

from ktbs.client.resource import Resource
from ktbs.common.root import KtbsRootMixin
from ktbs.common.utils import post_graph
from ktbs.namespaces import KTBS, SKOS
from rdfrest.utils import coerce_to_node

class KtbsRoot(KtbsRootMixin, Resource):
    """I implement a client proxy on the root of a kTBS.
    """

    RDF_MAIN_TYPE = KTBS.KtbsRoot

    def create_base(self, id=None, label=None, graph=None):
        """Create a new base in this kTBS.

        :param id: see :ref:`ktbs-resource-creation`
        :param label: explain.
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.client.base.Base`
        """
        #pylint: disable-msg=W0622
        #    redefining built-in 'id'
        node = coerce_to_node(id, self.uri)
        if graph is None:
            graph = Graph()
        graph.add((self.uri, _HAS_BASE, node))
        graph.add((node, _RDF_TYPE, _BASE))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))
        rheaders, _rcontent = post_graph(graph, self.uri)
        created_uri = rheaders['location']
        return self.factory(created_uri, _BASE)

_RDF_TYPE = RDF.type
_BASE = KTBS.Base
_HAS_BASE = KTBS.hasBase
