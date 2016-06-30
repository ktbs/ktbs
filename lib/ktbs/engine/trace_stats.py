#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
I provide the implementation of kTBS obsel collections.
"""
from itertools import chain
from logging import getLogger

from rdflib import Graph, Literal, RDF, BNode
from rdflib.namespace import Namespace
from rdflib.plugins.sparql.processor import prepareQuery

from rdfrest.exceptions import CanNotProceedError, InvalidParametersError, \
    MethodNotAllowedError
from rdfrest.cores.local import NS as RDFREST
from rdfrest.util import Diagnosis
from .resource import KtbsResource, METADATA
from .obsel import get_obsel_bounded_description
from .trace_obsels import _REFRESH_VALUES
from ..api.trace_stats import TraceStatisticsMixin
from ..namespace import KTBS


LOG = getLogger(__name__)

NS = Namespace('http://tbs-platform.org/2016/trace-stats#')

class TraceStatistics(TraceStatisticsMixin, KtbsResource):
    """I provide the implementation of ktbs:AbstractTraceObsels
    """
    ######## Public methods ########
    # (only available in the local implementation)

    @classmethod
    def init_graph(cls, graph, stats_uri, trace_uri):
        """I populate `graph` as an empty obsel collection for the given trace.
        """
        graph.add((trace_uri, KTBS.hasTraceStatistics, stats_uri))
        graph.add((stats_uri, RDF.type, cls.RDF_MAIN_TYPE))

    ######## ICore implementation  ########

    __forcing_state_refresh = None

    def get_state(self, parameters=None):
        """I override `~rdfrest.cores.ICore.get_state`:meth:

        I support parameter 'refresh' to bypass the updating of the obsels,
        or force a recomputation of the trace.
        """
        self.force_state_refresh(parameters)
        return super(TraceStatistics, self).get_state(parameters)

    def force_state_refresh(self, parameters=None):
        """I override `~rdfrest.cores.ICore.force_state_refresh`:meth:

        I recompute the obsels if needed.
        """
        refresh_param = (_REFRESH_VALUES[parameters.get("refresh")]
                         if parameters else 1)
        if refresh_param == 0 or self.__forcing_state_refresh:
            return

        if (self.metadata.value(self.uri, METADATA.dirty) is None
            and refresh_param < 2):
            return

        self.__forcing_state_refresh = True
        try:
            LOG.debug('refreshing <{}>'.format(self.uri))
            trace = self.trace
            trace.obsel_collection.force_state_refresh(parameters)

            # Avoid passing refresh parameter to edit()
            with self.edit(None, _trust=True) as editable:
                editable.remove((None, None, None))
                self.init_graph(editable, self.uri, trace.uri)
                self._populate(editable, trace)
                self.metadata.remove((self.uri, METADATA.dirty, None))
        finally:
            del self.__forcing_state_refresh

    def edit(self, parameters=None, clear=False, _trust=False):
        """I override :meth:`.KtbsResource.edit`.
        """
        if not _trust:
            raise MethodNotAllowedError(
                "Can not directly edit obsels of computed trace.")
        else:
            return super(TraceStatistics, self).edit(parameters, clear,
                                                         _trust)

    def delete(self, parameters=None, _trust=False):
        """I override :meth:`.KtbsResource.delete`.

        You can not delete a trace statistics.
        """
        if _trust:
            # this should only be set of the owning trace
            super(TraceStatistics, self).delete(None, _trust)
        else:
            self.check_parameters(parameters, "delete")
            raise MethodNotAllowedError("Can not delete trace statistics; "
                                        "delete its owning trace instead.")


    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.TraceStatistics

    @classmethod
    def create(cls, service, uri, new_graph):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.create`

        I mark this resource as dirty.
        """
        super(TraceStatistics, cls).create(service, uri, new_graph)
        metadata = service.get_metadata_graph(uri)
        metadata.add((uri, METADATA.dirty, Literal('yes')))

    def check_parameters(self, to_check, parameters, method):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.check_parameters`

        I also convert parameters values from strings to usable datatypes.
        """
        to_check_again = []
        if to_check is not None:
            if method in ("get_state", "force_state_refresh"):
                for key in to_check:
                    if key == "refresh":
                        val = parameters[key]
                        if val not in _REFRESH_VALUES:
                            raise InvalidParametersError(
                                "Invalid value for 'refresh' (%s)" % val)
                    else:
                        to_check_again.append(key)
            else:
                to_check_again = to_check

        if to_check_again:
            super(TraceStatistics, self).check_parameters(to_check_again, parameters, method)

    ######## Private  ########

    def _populate(self, graph, trace):
        """I populate graph with statistics about trace.

        :type graph: :class:`rdflib.Graph`

        """
        obsels_graph = trace.obsel_collection.state
        initNs = { '': unicode(KTBS.uri) }
        initBindings = { 'trace': trace.uri }

        # Obsel count
        count_result = obsels_graph.query(COUNT_OBSELS, initNs=initNs,
                                          initBindings=initBindings)
        count = count_result.bindings[0]['c']
        graph.add((trace.uri, NS.obselCount, count))

        # Obsel type statistics
        if count.value > 0:
            count_type_result = obsels_graph.query(COUNT_OBSEL_TYPES, initNs=initNs,
                                                   initBindings=initBindings)

            if (count_type_result is not None and
               len(count_type_result.bindings) > 0 and
               len(count_type_result.bindings[0]) > 0):
                for res in  count_type_result.bindings:
                    ot_infos = BNode()

                    graph.add((ot_infos, NS.nb, res['nb']))
                    graph.add((ot_infos, NS.hasObselType, res['t']))

                    graph.add((trace.uri, NS.obselCountPerType, ot_infos))

        # Duration statistics
        duration_result = obsels_graph.query(DURATION_TIME, initNs=initNs,
                                             initBindings=initBindings)

        if (duration_result is not None and
            len(duration_result.bindings) > 0 and
            len(duration_result.bindings[0]) > 0):
            graph.add((trace.uri, NS.minTime, duration_result.bindings[0]['minb']))
            graph.add((trace.uri, NS.maxTime, duration_result.bindings[0]['maxe']))
            graph.add((trace.uri, NS.duration, duration_result.bindings[0]['duration']))


COUNT_OBSELS='SELECT (COUNT(?o) as ?c) { ?o :hasTrace ?trace }'
COUNT_OBSEL_TYPES= 'SELECT ?t (count(?o) as ?nb) (min(?b) as ?begin) { ?o :hasTrace ?trace; :hasBegin ?b ; a ?t . } ' \
                   'GROUP BY ?t ORDER BY ?t'
DURATION_TIME="""SELECT ?minb ?maxe ((?maxe - ?minb) as ?duration) where {
SELECT (min(?b) as ?minb) (max(?e) as ?maxe)  where {
        ?o :hasTrace ?trace ;
           :hasBegin ?b ;
           :hasEnd ?e .
    }}
"""