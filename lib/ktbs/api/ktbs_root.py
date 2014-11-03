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
I provide the pythonic interface of ktbs:KtbsRoot .
"""
from rdflib import Graph, Literal, RDF

from rdfrest.cores.factory import factory as universal_factory
from rdfrest.util import coerce_to_node, coerce_to_uri
from rdfrest.wrappers import register_wrapper
from .resource import KtbsResourceMixin
from ..namespace import KTBS
from ..utils import extend_api, SKOS


@register_wrapper(KTBS.KtbsRoot)
@extend_api
class KtbsRootMixin(KtbsResourceMixin):
    """
    I provide the pythonic interface common to ktbs root.
    """

    ######## Abstract kTBS API ########

    def iter_builtin_methods(self):
        """
        I list all the builtin methods implemented by this kTBS.
        """
        for obs in self.state.objects(self.uri, KTBS.hasBuiltinMethod):
            yield universal_factory(obs, _rdf_type=KTBS.BuiltinMethod)

    def iter_bases(self):
        """
        I iter over all elements owned by this base.
        """
        self_factory = self.factory
        for obs in self.state.objects(self.uri, KTBS.hasBase):
            yield self_factory(obs)

    def get_builtin_method(self, uri):
        """I return the built-in method identified by `uri` if supported.
        """
        uri = coerce_to_uri(uri)
        if (self.uri, KTBS.hasBuiltinMethod, uri) in self.state:
            return universal_factory(uri, _rdf_type=KTBS.BuiltinMethod)
        else:
            return None

    def get_base(self, id):
        """
        I return the base corresponding to the given URI.
        """
        # redefining built-in 'id' #pylint: disable-msg=W0622
        base_uri = coerce_to_uri(id, self.uri)
        return self.factory(base_uri, KTBS.Base)
        # must be a .base.BaseMixin

    def create_base(self, id=None, label=None, graph=None):
        """Create a new base in this kTBS.

        :param id: see :ref:`ktbs-resource-creation`
        :param label: TODO DOC explain
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.client.base.Base`
        """
        # redefining built-in 'id' #pylint: disable-msg=W0622
        trust = graph is None  and  id is None
        node = coerce_to_node(id, self.uri)
        if graph is None:
            graph = Graph()
        graph.add((self.uri, KTBS.hasBase, node))
        graph.add((node, RDF.type, KTBS.Base))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))
        uris = self.post_graph(graph, None, trust, node, KTBS.Base)
        assert len(uris) == 1
        return self.factory(uris[0], KTBS.Base)
        # must be a .base.BaseMixin
