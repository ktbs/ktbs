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
from httplib2 import Http
from rdflib import BNode, Graph, RDF
#from rdfrest.client import ProxyStore

from ktbs.client.resource import Resource, RESOURCE_MAKER
from ktbs.common.root import KtbsRootMixin
from ktbs.common.utils import coerce_to_uri
from ktbs.namespaces import KTBS

class KtbsRoot(KtbsRootMixin, Resource):
    """I implement a client proxy on the root of a kTBS.
    """

    def create_base(self, id=None, graph=None):
        """Create a new base in this kTBS.
        id: either None, a relative URI or a BNode present in graph
        graph: if not none, may contain additional properties for the new base
        """
        #pylint: disable-msg=W0622
        #    redefining built-in 'id'
        if id is None:
            uri = BNode()
        elif isinstance(id, BNode):
            uri = id
        else:
            uri = coerce_to_uri(id, self.uri)
        if graph is None:
            graph = Graph()
        graph.add((uri, _RDF_TYPE, _BASE))
        graph.add((self.uri, _HAS_BASE, uri))
        data = graph.serialize(format="n3")
        headers = {
            'content-type': 'text/turtle',
            }
        rheaders, _rcontent = Http().request(self.uri, 'POST', data,
                                           headers=headers)
        if rheaders.status / 100 != 2:
            raise ValueError(rheaders) # TODO make a better exception
        created_uri = rheaders['location']
        # TODO MAJOR parse content and feed the graph to make_resource
        return self.make_resource(created_uri, _BASE)

RESOURCE_MAKER[KTBS.KtbsRoot] = KtbsRoot

_RDF_TYPE = RDF.type
_BASE = KTBS.Base
_HAS_BASE = KTBS.hasBase

# the following import ensures that Base is registered in RESOURCE_MAKER
import ktbs.client.base #pylint: disable-msg=W0611
# NB: we have to disable pylint W0611 (Unused import)
