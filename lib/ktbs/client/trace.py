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
I provide the client implementation of StoredTrace and ComputedTrace.
"""
from datetime import datetime

from ktbs.client.resource import Resource
from ktbs.common.computed_trace import ComputedTraceMixin
from ktbs.common.trace import StoredTraceMixin
from ktbs.common.utils import extend_api, post_graph
from ktbs.namespaces import KTBS
from ktbs.iso8601 import parse_date

from rdfrest.utils import coerce_to_node, coerce_to_uri
from rdfrest.client import ProxyStore

from rdflib import Graph, Literal, RDF, RDFS

@extend_api
class Trace(Resource):
    """TODO docstring
    """

    def __init__(self, uri, graph=None):
        """
        """
        Resource.__init__(self, uri, graph)
        obsel_uri = self._graph.value(self.uri, _HAS_OBSEL_COLLECTION)
        assert obsel_uri is not None
        self._obsels = Graph(ProxyStore({"uri":obsel_uri}),
                             identifier=obsel_uri)

    

class StoredTrace(StoredTraceMixin, Trace):
    """TODO docstring"""
    # TODO implement client-specifid methods

    RDF_MAIN_TYPE = KTBS.StoredTrace

    def create_obsel(self, id=None, type=None, begin=None, end=None, 
                     subject=None, attributes=None, relations=None, 
                     inverse_relations=None, source_obsels=None, label=None):
        """
        Creates a new obsel for the stored trace.

        :param id: see :ref:`ktbs-resource-creation`.
        :param type: Obsel type, defined by the Trace model.
        :param begin: Begin timestamp of the obsel, can be an int.
        :param end: End timestamp of the obsel, can be an int.
        :param subject: Subject of the obsel.
        :param attributes: explain.
        :param relations: explain.
        :param inverse_relations: explain.
        :param source_obsels: explain.
        :param label: explain.

        :rtype: `ktbs.client.obsel.Obsel`
        """
        # redefining built-in 'id' #pylint: disable=W0622                 
        if type is None:
            raise ValueError("type is mandatory for obsel creation")

        if begin is None:
            raise ValueError("begin timestamp is mandatory for obsel creation")

        if type is None:
            raise ValueError("end timestamp is mandatory for obsel creation")

        # TODO Which tests for type, begin and end parameters ?
        graph = Graph()
        obs = coerce_to_node(id, self.uri) # return BNode if id is None
        type_uri = coerce_to_uri(type, self.uri)
        graph.add((obs, RDF.type, type_uri))
        graph.add((obs, _HAS_TRACE, self.uri))

        if isinstance(begin, int):
            graph.add((obs, _HAS_BEGIN, Literal(begin)))
        else: # Will use _HAS_BEGIN_DT
            if isinstance(begin, basestring):
                begin = parse_date(begin)
            assert isinstance(begin, datetime)
            graph.add((obs, _HAS_BEGIN_DT, Literal(begin)))

        if isinstance(end, int):
            graph.add((obs, _HAS_END, Literal(end)))
        else: # Will use _HAS_END_DT
            if isinstance(end, basestring):
                end = parse_date(end)
            assert isinstance(end, datetime)
            graph.add((obs, _HAS_END_DT, Literal(end)))

        if subject is not None:
            graph.add((obs, _HAS_SUBJECT, Literal(subject)))

        if attributes is not None:
            assert isinstance(attributes, dict)
            for key, val in attributes.items():
                k_uri = coerce_to_uri(key)
                # TODO do something if val is a list
                graph.add((obs, k_uri, Literal(val)))

        if relations is not None:
            for rtype, other in relations:
                rtype_uri = coerce_to_uri(rtype)
                other_uri = coerce_to_uri(other)
                graph.add((obs, rtype_uri, other_uri))

        if inverse_relations is not None:
            for other, rtype in relations:
                other_uri = coerce_to_uri(other)
                rtype_uri = coerce_to_uri(rtype)
                graph.add((other_uri, rtype_uri, obs))

        if source_obsels is not None:
            for src in source_obsels:
                s_uri = coerce_to_uri(src)
                graph.add((obs, _HAS_SOURCE_OBSEL, s_uri))

        if label is not None:
            graph.add((obs, RDFS.label, Literal(label)))

        rheaders, _rcontent = post_graph(graph, self.uri)
        created_uri = rheaders['location']
        return self.factory(created_uri, _OBSEL)

class ComputedTrace(ComputedTraceMixin, Trace):
    """TODO docstring"""
    # TODO implement client-specifid methods

    RDF_MAIN_TYPE = KTBS.ComputedTrace


_HAS_BEGIN = KTBS.hasBegin
_HAS_BEGIN_DT = KTBS.hasBeginDT
_HAS_END = KTBS.hasEnd
_HAS_END_DT = KTBS.hasEndDT
_HAS_OBSEL_COLLECTION = KTBS.hasObselCollection
_HAS_SOURCE_OBSEL = KTBS.hasSourceObsel
_HAS_SUBJECT = KTBS.hasSubject
_HAS_TRACE = KTBS.hasTrace
_OBSEL = KTBS.Obsel

