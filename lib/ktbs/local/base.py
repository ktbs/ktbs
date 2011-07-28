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
I provide the local implementation of ktbs:Base .
"""
from rdflib import Graph, Literal, RDF
from rdfrest.mixins import RdfPostMixin
from rdfrest.utils import coerce_to_node, coerce_to_uri

from ktbs.common.base import BaseMixin
from ktbs.common.utils import extend_api
from ktbs.local.resource import Resource
from ktbs.namespaces import KTBS, SKOS

@extend_api
class Base(BaseMixin, RdfPostMixin, Resource):
    """
    I provide the pythonic interface common to ktbs root.
    """

    # KTBS API #

    def create_model(self, parents=(), label=None, id=None, graph=None):
        """Create a new trace-model in this base.

        :param id: see :ref:`ktbs-resource-creation`
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.local.model.Model`
        """
        # redefining built-in 'id' #pylint: disable-msg=W0622
        if parents is None:
            parents = () # abstract API allows None
        trust = id is None and graph is None
        node = coerce_to_node(id, self.uri)
        if graph is None:
            graph = Graph()
        graph.add((self.uri, KTBS.contains, node))
        graph.add((node, RDF.type, KTBS.TraceModel))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))
        for parent in parents:
            graph.add((node, KTBS.hasParentModel, coerce_to_uri(parent)))
        return self._post_or_trust(trust, Model, node, graph)

    def create_method(self, parent, parameters=None, label=None,
                      id=None, graph=None):
        """Create a new method in this base.
        
        :param id: see :ref:`ktbs-resource-creation`
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.local.method.Method`
        """
        # redefining built-in 'id' #pylint: disable-msg=W0622
        if parameters is None:
            parameters = {}
        trust = id is None and graph is None
        node = coerce_to_node(id, self.uri)
        if graph is None:
            graph = Graph()
        graph.add((self.uri, KTBS.contains, node))
        graph.add((node, RDF.type, KTBS.Method))
        graph.add((node, KTBS.hasParentMethod, coerce_to_uri(parent)))
        for key, value in parameters.iteritems():
            if "=" in key:
                raise ValueError("Invalid parameter name '%s'" % key)
            graph.add((node, KTBS.hasParameter,
                       Literal("%s=%s" % (key, value))))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))
        return self._post_or_trust(trust, Method, node, graph)
            
    # RDF-REST API #

    RDF_MAIN_TYPE = KTBS.Base

    RDF_POSTABLE_IN = [ KTBS.hasBase, ]

    def check_posted_graph(self, created, new_graph):
        """I override `rdfrest.mixins.RdfPostMixin.check_posted_graph`.

        I check that only instances of ktbs:Base are posted.
        """
        if (self.uri, KTBS.contains, created) not in new_graph:
            return "No ktbs:contains between Base and created resource."
        for rdf_type in new_graph.objects(created, RDF.type):
            if rdf_type in _ALLOWED_TYPES:
                break
        else:
            return "Posted resource is not supported by ktbs:Base"
        return super(Base, self).check_posted_graph(created, new_graph)


class BaseResource(Resource):
    """Common properties for all resources contained in Base.
    """

    RDF_POSTABLE_IN = [ KTBS.contains, ]
    RDF_CARDINALITY_IN = [ (KTBS.contains, 1, 1), ]


# these imports must be in the end, because import BaseResource
from ktbs.local.model import Model
from ktbs.local.method import Method

_ALLOWED_TYPES = frozenset([
                        KTBS.ComputedTrace,
                        KTBS.Method,
                        KTBS.StoredTrace,
                        KTBS.TraceModel,
                        ])
