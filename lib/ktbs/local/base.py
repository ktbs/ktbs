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
from md5 import md5
from rdflib import Graph, Literal, RDF
from rdfrest.mixins import RdfPutMixin
from rdfrest.resource import Resource
from rdfrest.utils import coerce_to_node, coerce_to_uri
from time import time

from ktbs.common.base import BaseMixin
from ktbs.common.utils import extend_api
from ktbs.local.resource import KtbsPostMixin, KtbsResourceMixin
from ktbs.local.service import KtbsService
from ktbs.namespaces import KTBS, SKOS

@extend_api
class Base(BaseMixin, KtbsPostMixin, RdfPutMixin, Resource):
    """I implement a local KTBS Base.
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
        node = coerce_to_node(id, self.uri)
        trust_graph = graph is None
        if graph is None:
            graph = Graph()
        graph.add((self.uri, KTBS.contains, node))
        graph.add((node, RDF.type, KTBS.TraceModel))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))
        for parent in parents:
            graph.add((node, KTBS.hasParentModel, coerce_to_uri(parent)))
        return self._post_or_trust(Model, node, graph, trust_graph)

    def create_method(self, parent, parameters=None, label=None,
                      id=None, graph=None):
        """Create a new method in this base.
        
        :param id: see :ref:`ktbs-resource-creation`
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.local.method.Method`
        """
        # redefining built-in 'id' #pylint: disable-msg=W0622
        parent_uri = coerce_to_uri(parent)
        if parameters is None:
            parameters = {}
        node = coerce_to_node(id, self.uri)

        trust_graph = graph is None
        if trust_graph:
            # we need to check some integrity constrains,
            # because the graph may be blindly trusted
            #
            # NB: the following code is *different* from the code that does
            # those checks in check_new_graph, so it can not be factorized

            acceptable = parent_uri.startswith(self.uri) \
                or KtbsService.has_builtin_method(parent_uri)
            if not acceptable:
                raise ValueError("Invalid parent method: <%s>"
                                       % parent_uri)
            for key in parameters:
                if "=" in key:
                    raise ValueError("Invalid parameter name '%s'" % key)

            graph = Graph()

        graph.add((self.uri, KTBS.contains, node))
        graph.add((node, RDF.type, KTBS.Method))
        graph.add((node, KTBS.hasParentMethod, parent_uri))
        for key, value in parameters.iteritems():
            graph.add((node, KTBS.hasParameter,
                       Literal("%s=%s" % (key, value))))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))
        return self._post_or_trust(Method, node, graph, trust_graph)

    def create_stored_trace(self, model, origin=None, default_subject=None,
                            label=None, id=None, graph=None):
        """Create a new stored trace in this base.
        
        :param id: see :ref:`ktbs-resource-creation`
        :param graph: see :ref:`ktbs-resource-creation`

        :rtype: `ktbs.local.method.StoredTrace`
        """
        # redefining built-in 'id' #pylint: disable-msg=W0622
        node = coerce_to_node(id, self.uri)
        if origin is None:
            token = "%s%s" % (time(), node)
            origin = "o" + md5(token).hexdigest()

        trust_graph = graph is None
        if trust_graph:
            # we need to check some integrity constrains,
            # because the graph may be blindly trusted
            #
            # NB: the following code is *different* from the code that does
            # those checks in check_new_graph, so it can not be factorized

            # TODO MINOR check trace timestamps if provided

            graph = Graph()

        graph.add((self.uri, KTBS.contains, node))
        graph.add((node, RDF.type, KTBS.StoredTrace))
        graph.add((node, KTBS.hasModel, coerce_to_uri(model)))
        graph.add((node, KTBS.hasOrigin, Literal(origin)))
        if default_subject:
            graph.add((node, KTBS.hasDefaultSubject, Literal(default_subject)))
        if label:
            graph.add((node, SKOS.prefLabel, Literal(label)))
        return self._post_or_trust(StoredTrace, node, graph, trust_graph)
        

    def ack_new_child(self, child_uri, child_type):
        """Override :meth:`ktbs.local.resource.PostableResource.ack_new_child`
        """
        super(Base, self).ack_new_child(child_uri, child_type)
        with self._edit as g:
            g.add((self.uri, KTBS.contains, child_uri))
            g.add((child_uri, RDF.type, child_type))
            
    # RDF-REST API #

    RDF_MAIN_TYPE = KTBS.Base

    RDF_POSTABLE_IN = [ KTBS.hasBase, ]

    def find_created(self, new_graph, query=None):
        """I override `rdfrest.mixins.RdfPostMixin.find_created`.

        I only search for nodes that this base ktbs:contains .
        """
        if query is None:
            query = "SELECT ?c WHERE { <%%(uri)s> <%s> ?c }" % KTBS.contains
        return super(Base, self).find_created(new_graph, query)

    KTBS_CHILDREN_TYPES = [ # used by check_posted_graph
            KTBS.ComputedTrace,
            KTBS.Method,
            KTBS.StoredTrace,
            KTBS.TraceModel,
            ]


class InBaseMixin(KtbsResourceMixin):
    """Common properties for all resources contained in Base.
    """

    RDF_POSTABLE_IN = [ KTBS.contains, ]
    RDF_CARDINALITY_IN = [ (KTBS.contains, 1, 1), ]


# these imports must be in the end to ensure a consistent import order
from ktbs.local.model import Model
from ktbs.local.method import Method
from ktbs.local.trace import StoredTrace
