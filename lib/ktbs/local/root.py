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
I provide the local implementation of ktbs:KtbsRoot .
"""
from rdflib import Graph, Literal, RDF
from rdfrest.mixins import RdfPostMixin
from rdfrest.utils import coerce_to_node

from ktbs.common.root import KtbsRootMixin
from ktbs.common.utils import extend_api
from ktbs.local.resource import PostableResource
from ktbs.namespaces import KTBS, SKOS

@extend_api
class KtbsRoot(KtbsRootMixin, PostableResource, RdfPostMixin):
    """I implement a local KTBS root.
    """

    # KTBS API #

    def create_base(self, label=None, id=None, graph=None):
        """Create a new base in this kTBS.

        :param id: see :ref:`ktbs-resource-creation`
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.local.model.Base`
        """
        #pylint: disable-msg=W0622
        #    redefining built-in 'id'
        node = coerce_to_node(id, self.uri)
        trust_graph = graph is None
        if graph is None:
            graph = Graph()
        graph.add((self.uri, _HAS_BASE, node))
        graph.add((node, RDF.type, _BASE))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))
        return self._post_or_trust(Base, node, graph, trust_graph)

    def ack_new_child(self, child_uri):
        """I override
        :method:`ktbs.local.resource.PostableResource.ack_new_child`
        """
        super(KtbsRoot, self).ack_new_child(child_uri)
        with self._edit as g:
            g.add((self.uri, _HAS_BASE, child_uri))
                    
    # RDF-REST API #

    RDF_MAIN_TYPE = KTBS.KtbsRoot
    RDF_POSTABLE_OUT = [KTBS.hasBuiltinMethod,]

    def find_created(self, new_graph, query=None):
        """I override `rdfrest.mixins.RdfPostMixin.find_created`.

        I only search for nodes with outgoing ktbs:hasBase .
        """
        if query is None:
            query = "SELECT ?c WHERE { <%%(uri)s> <%s> ?c }" % _HAS_BASE
        return super(KtbsRoot, self).find_created(new_graph, query)
        
    KTBS_CHILDREN_TYPES = [KTBS.Base,] # used by check_posted_graph

_BASE = KTBS.Base
_HAS_BASE = KTBS.hasBase

# these imports must be in the end to ensure a consistent import order
from ktbs.local.base import Base
