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

from ktbs.client.resource import Resource, RESOURCE_MAKER
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


    def iter_obsels(self, begin=None, end=None, reverse=False):
        """
        Iter over the obsels of this trace.

        The obsels are sorted by their end timestamp, then their begin
        timestamp, then their identifier. If reverse is true, the order is
        inversed.

        If given, begin and/or end are interpreted as the (included)
        boundaries of an interval; only obsels entirely contained in this
        interval will be yielded.

        * begin: an int, datetime or Obsel
        * end: an int, datetime or Obsel
        * reverse: an object with a truth value

        NB: the order of "recent" obsels may vary even if the trace is not
        amended, since collectors are not bound to respect the order in begin
        timestamps and identifiers.
        """
        if begin or end or reverse:
            raise NotImplementedError(
                "iter_obsels parameters not implemented yet")
            # TODO MAJOR implement parameters of iter_obsels
        # TODO MAJOR when rdflib supports ORDER BY, make SPARQL do the sorting
        query_str = """
            SELECT ?b ?e ?obs WHERE {
                ?obs <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> <%s> ;
                     <http://liris.cnrs.fr/silex/2009/ktbs#hasBegin> ?b ;
                     <http://liris.cnrs.fr/silex/2009/ktbs#hasEnd> ?e
            }
        """ % self.uri # TODO simplify once 
        obsels_graph = self._obsels
        tuples = list(obsels_graph.query(query_str))
        tuples.sort() # TODO remove this hack once rdflib supports 'ORDER BY'
        make_resource = self.make_resource
        for _, _, obs in tuples:
            yield make_resource(obs, _OBSEL, obsels_graph)

    

class StoredTrace(StoredTraceMixin, Trace):
    """TODO docstring"""
    # TODO implement client-specifid methods

    def create_obsel(self, type, begin, end, subject=None,
                     attributes=None, relations=None, inverse_relations=None,
                     source_obsels=None, label=None, id=None):
        """
        Creates a new obsel for the stored trace.

        :param type: Obsel type, defined by the Trace model.
        :param begin: Begin timestamp of the obsel, can be an int.
        :param end: End timestamp of the obsel, can be an int.
        :param subject: Subject of the obsel.
        :param attributes: explain.
        :param relations: explain.
        :param inverse_relations: explain.
        :param source_obsels: explain.
        :param label: explain.
        :param id: see :ref:`ktbs-resource-creation`.

        :rtype: `ktbs.client.obsel.Obsel`
        """
        # redefining built-in 'id' #pylint: disable=W0622                 

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
            assert isinstance(relations, dict)
            for key, val in relations.items():
                # TODO MAJOR replace with list of pairs, to allow multiple
                # values for the same relation type?
                k_uri = coerce_to_uri(key)
                v_uri = coerce_to_uri(val)
                graph.add((obs, k_uri, v_uri))

        if inverse_relations is not None:
            assert isinstance(inverse_relations, dict)
            for key, val in relations.items():
                # TODO MAJOR replace with list of pairs, to allow multiple
                # values for the same relation type?
                k_uri = coerce_to_uri(key)
                v_uri = coerce_to_uri(val)
                graph.add((v_uri, k_uri, obs))

        if source_obsels is not None:
            for src in source_obsels:
                s_uri = coerce_to_uri(src)
                graph.add((obs, _HAS_SOURCE_OBSEL, s_uri))

        if label is not None:
            graph.add((obs, RDFS.label, Literal(label)))

        rheaders, _rcontent = post_graph(graph, self.uri)
        created_uri = rheaders['location']
        return self.make_resource(created_uri, _OBSEL)

class ComputedTrace(ComputedTraceMixin, Trace):
    """TODO docstring"""
    # TODO implement client-specifid methods

RESOURCE_MAKER[KTBS.StoredTrace] = StoredTrace
RESOURCE_MAKER[KTBS.ComputedTrace] = ComputedTrace

_HAS_BEGIN = KTBS.hasBegin
_HAS_BEGIN_DT = KTBS.hasBeginDT
_HAS_END = KTBS.hasEnd
_HAS_END_DT = KTBS.hasEndDT
_HAS_OBSEL_COLLECTION = KTBS.hasObselCollection
_HAS_SOURCE_OBSEL = KTBS.hasSourceObsel
_HAS_SUBJECT = KTBS.hasSubject
_HAS_TRACE = KTBS.hasTrace
_OBSEL = KTBS.Obsel

# the following import ensures that Obsel are registered in RESOURCE_MAKER
import ktbs.client.obsel #pylint: disable-msg=W0611
# NB: we have to disable pylint W0611 (Unused import)
