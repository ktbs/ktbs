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
from logging import getLogger

from rdflib import Literal, RDF, BNode, Variable
from rdflib.namespace import Namespace

from rdfrest.exceptions import InvalidParametersError, MethodNotAllowedError
from .lock import WithLockMixin
from .resource import KtbsResource, METADATA
from .trace_obsels import _REFRESH_VALUES
from ..api.trace_stats import TraceStatisticsMixin
from ..namespace import KTBS


LOG = getLogger(__name__)

NS = Namespace('http://tbs-platform.org/2016/trace-stats#')
_PLUGINS = []

def add_plugin(f):
    _PLUGINS.append(f)

def remove_plugin(f):
    _PLUGINS.remove(f)

class TraceStatistics(TraceStatisticsMixin, WithLockMixin, KtbsResource):
    """I provide the implementation of TraceStatistics
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

        with self.lock(self):
            self.__forcing_state_refresh = True
            try:
                LOG.debug('refreshing <{}>'.format(self.uri))
                trace = self.trace
                trace.force_state_refresh()
                trace.obsel_collection.force_state_refresh(parameters)

                metadata = self.metadata
                seen_trc_etag = metadata.value(self.uri, METADATA.traceEtag, None)
                seen_obs_etag = metadata.value(self.uri, METADATA.obselsEtag, None)
                last_trc_etag = self.trace.iter_etags().next()
                last_obs_etag = self.trace.obsel_collection.get_etag()
                dirty =  seen_trc_etag != last_trc_etag  or  seen_obs_etag != last_obs_etag

                if not dirty and refresh_param < 2:
                    return

                # Avoid passing refresh parameter to edit()
                with self.edit(None, _trust=True) as editable:
                    editable.remove((None, None, None))
                    self.init_graph(editable, self.uri, trace.uri)
                    self._populate(editable, trace)
                    self.metadata.set((self.uri, METADATA.traceEtag, Literal(last_trc_etag)))
                    self.metadata.set((self.uri, METADATA.obselsEtag, Literal(last_obs_etag)))
            finally:
                del self.__forcing_state_refresh

    def edit(self, parameters=None, clear=False, _trust=False):
        """I override :meth:`.KtbsResource.edit`.
        """
        if not _trust:
            raise MethodNotAllowedError(
                "@stats is read-only")
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

        # Obsel count
        ## using initBinfings would be cleaner, but Virtuoso does not supports it :-()
        count_obsels = COUNT_OBSELS.replace('$trace', trace.uri.n3())
        count_result = obsels_graph.query(count_obsels, initNs=initNs)
        count = count_result.bindings[0]['c']
        graph.add((trace.uri, NS.obselCount, count))

        # Duration statistics
        ## using initBinfings would be cleaner, but Virtuoso does not supports it :-()
        duration_time = DURATION_TIME.replace('$trace', trace.uri.n3())
        duration_result = obsels_graph.query(duration_time, initNs=initNs)

        if (duration_result is not None
            and len(duration_result.bindings) > 0
            and len(duration_result.bindings[0]) > 0):

            b = duration_result.bindings[0]
            graph.add((trace.uri, NS.minTime, b['minb']))
            graph.add((trace.uri, NS.maxTime, b['maxe']))
            graph.add((trace.uri, NS.duration, b['duration']))

        for plugin in _PLUGINS:
            try:
                plugin(graph, trace)
            except BaseException as ex:
                LOG.error("Error while populating <%s>", self.uri)
                LOG.exception(ex)


COUNT_OBSELS='SELECT (COUNT(?o) as ?c) { ?o :hasTrace $trace }'
DURATION_TIME="""
SELECT ?minb ?maxe ((?maxe - ?minb) as ?duration)
where {
SELECT (min(?b) as ?minb) (max(?e) as ?maxe)
where {
        ?o :hasTrace $trace ;
           :hasBegin ?b ;
           :hasEnd ?e .
    }
}
"""
