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
from ktbs.local.base import Base
from ktbs.local.resource import Resource
from ktbs.namespaces import KTBS, SKOS

@extend_api
class KtbsRoot(KtbsRootMixin, RdfPostMixin, Resource):
    """
    I provide the pythonic interface common to ktbs root.
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
        trust = id is None and graph is None
        node = coerce_to_node(id, self.uri)
        if graph is None:
            graph = Graph()
        graph.add((self.uri, _HAS_BASE, node))
        graph.add((node, RDF.type, _BASE))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))
        ret = self._post_or_trust(trust, Base, node, graph)
        with self._edit as g:
            g.add((self.uri, _HAS_BASE, ret.uri))
        return ret
            
    # RDF-REST API #

    RDF_MAIN_TYPE = KTBS.KtbsRoot
    RDF_POSTABLE_OUT = [KTBS.hasBuiltinMethod,]

    @classmethod
    def create_root_graph(cls, uri, service):
        """I override `rdfrest.resource.Resource.create_root_graph`.

        I populate the graph with KtbsRoot specific data.
        """
        graph = super(KtbsRoot, cls).create_root_graph(uri, service)
        for method_uri in service.builtin_methods():
            graph.add((uri, KTBS.hasBuiltinMethod, method_uri))
        return graph

    def check_posted_graph(self, created, new_graph):
        """I override `rdfrest.mixins.RdfPostMixin.check_posted_graph`.

        I check that only instances of ktbs:Base are posted.
        """
        if (self.uri, KTBS.hasBase, created) not in new_graph:
            return "No ktbs:hasBase between KtbsRoot and created Base."
        if (created, RDF.type, KTBS.Base) not in new_graph:
            return "Posted resource is not a ktbs:Base."
        return super(KtbsRoot, self).check_posted_graph(created, new_graph)


_BASE = KTBS.Base
_HAS_BASE = KTBS.hasBase
