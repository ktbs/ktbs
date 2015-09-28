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

from rdflib import Graph, Literal, RDF
from rdflib.plugins.sparql.processor import prepareQuery

from rdfrest.exceptions import CanNotProceedError, InvalidParametersError, \
    MethodNotAllowedError
from rdfrest.cores.local import NS as RDFREST
from .resource import KtbsResource, METADATA
from .obsel import get_obsel_bounded_description
from ..api.trace_obsels import AbstractTraceObselsMixin
from ..namespace import KTBS


LOG = getLogger(__name__)

class AbstractTraceObsels(AbstractTraceObselsMixin, KtbsResource):
    """I provide the implementation of ktbs:AbstractTraceObsels
    """
    ######## Public methods ########
    # (only available in the local implementation)

    @classmethod
    def init_graph(cls, graph, obsels_uri, trace_uri):
        """I populate `graph` as an empty obsel collection for the given trace.
        """
        graph.add((trace_uri, KTBS.hasObselCollection, obsels_uri))
        graph.add((obsels_uri, RDF.type, cls.RDF_MAIN_TYPE))


    def get_etag(self):
        """Return the entity tag.

        This tag changes at every modification of the obsel collection.
        """
        return str(self.metadata.value(self.uri, RDFREST.etag))
    def set_etag(self, val):
        """Set the etag.

        :see-also: `get-etag`:meth:
        """
        self.metadata.set((self.uri, RDFREST.etag, "%se" % val))
    etag = property(get_etag, set_etag)

    def get_str_mon_tag(self):
        """Return the strictly monotonic tag.

        This tag only changes when the obsel collection is modified in a
        non-strictly monotonic way.

        In other words, it does not change as long as obsels are added after
        all existing obsels, without any relation to previous obsels.
        """
        return str(self.metadata.value(self.uri, METADATA.str_mon_tag))
    def set_str_mon_tag(self, val):
        """Set the str_mon_tag.

        :see-also: `get-str_mon_tag`:meth:
        """
        self.metadata.set((self.uri, METADATA.str_mon_tag, "%ss" % val))
    str_mon_tag = property(get_str_mon_tag, set_str_mon_tag)

    def get_pse_mon_tag(self):
        """Return the pseudo-monotonic tag.

        This tag only changes when the obsel collection is modified in a
        non-pseudo-monotonic way.

        In other words, it does not change as arcs are only added between obsels
        withing the pseudo-monotonicity range
        (see `~.trace.AbstractTrace.get_pseudomon_range>`:meth:) of the trace.
        """
        return str(self.metadata.value(self.uri, METADATA.pse_mon_tag))
    def set_pse_mon_tag(self, val):
        """Set the pse_mon_tag.

        :see-also: `get-pse_mon_tag`:meth:
        """
        self.metadata.set((self.uri, METADATA.pse_mon_tag, "%sp" % val))
    pse_mon_tag = property(get_pse_mon_tag, set_pse_mon_tag)

    def get_log_mon_tag(self):
        """Return the logically monotonic tag.

        This tag only changes when the obsel collection is modified in a
        non-monotonic way.

        In other words, it does not change as long as arcs are only added to
        the graph, not removed.
        """
        return str(self.metadata.value(self.uri, METADATA.log_mon_tag))
    def set_log_mon_tag(self, val):
        """Set the log_mon_tag.

        :see-also: `get-log_mon_tag`:meth:
        """
        self.metadata.set((self.uri, METADATA.log_mon_tag, "%sl" % val))
    log_mon_tag = property(get_log_mon_tag, set_log_mon_tag)


    _in_add_graph = False  # used to inform ack_edit not to update last_obsel

    def add_graph(self, graph, _trust=True):
        """Add all the arcs in `graph` to this obsel collection's state.

        This should be used instead of the
        `~rdfrest.cores.ICore.edit`:meth: context when no arc has to
        be removed, as it will not change the
        `log_mon_tag`:meth`.
        """
        old_str_mon_tag = self.metadata.value(self.uri, METADATA.str_mon_tag)
        old_pse_mon_tag = self.metadata.value(self.uri, METADATA.pse_mon_tag)
        old_log_mon_tag = self.metadata.value(self.uri, METADATA.log_mon_tag)
        old_last_obsel = self.metadata.value(self.uri, METADATA.last_obsel)

        with self.edit(_trust=_trust) as editable:
            # inner context is used to apply the changes and have them
            # go through check_new_graph
            _add = editable.add
            for triple in graph:
                _add(triple)
            
            # find the last obsel (this is quicker than what ack_edit does;
            # by setting self._in_add_graph, we thus inform ack_edit to skip
            # its own search)
            new_last_obsel, new_last_end = self._get_new_last_obsel(
                graph, old_last_obsel)
            self.metadata.set((self.uri, METADATA.last_obsel, new_last_obsel))
            self._in_add_graph = True

        # inspect the changes we just made...
        if old_last_obsel is None:
            # all obsels are new, so change is monotonic
            str_mon, pse_mon = True, True
        else:
            old_last_end = int(self.state.value(old_last_obsel, KTBS.hasEnd))
            pse_mon_limit = new_last_end - self.trace.pseudomon_range
            str_mon, pse_mon = self._detect_mon_change(graph, old_last_end,
                                                       pse_mon_limit)

        # ...and reset monotonicity tags accordingly
        # NB: log_mon would always be true, as we only *add* triples
        self.metadata.set((self.uri, METADATA.log_mon_tag, old_log_mon_tag))
        if pse_mon:
            self.metadata.set((self.uri, METADATA.pse_mon_tag, old_pse_mon_tag))
        if str_mon:
            self.metadata.set((self.uri, METADATA.str_mon_tag, old_str_mon_tag))


    ######## ICore implementation  ########

    def get_state(self, parameters=None):
        """I override `~rdfrest.cores.ICore.get_state`:meth:

        I support some parameters to get "slices" of the obsel collection.
        Note that, contrarily to what the interface specifies, slice graphs are
        static copies of the data; they are not automatically updated, and
        the slicing parameters are not supported by
        `~rdfrest.cores.ICore.force_state_refresh`:meth.

        I consider an empty dict as equivalent to no dict.
        """
        # TODO LATER find a way to generate dynamic slices?
        # on the other hand, this is only by http_server when a query_string
        # is provided, and http_server does not require dynamic graphs, so...

        if (not parameters # empty dict is equivalent to no dict
            or "refresh" in parameters and len(parameters) == 1): 
            return super(AbstractTraceObsels, self).get_state(None)
        else:
            self.check_parameters(parameters, "get_state")
            graph = Graph(identifier=self.uri)
            graph_add = graph.add

            # fill graph with data about the obsel collection
            for triple in self.state.triples((self.uri, None, None)):
                graph_add(triple)
            for triple in self.state.triples((None, None, self.uri)):
                graph_add(triple)

            # build SPARQL query to retrieve matching obsels
            # NB: not sure if caching the parsed query would be beneficial here
            query_filter = []
            query_epilogue = "ORDER BY ?e ?b"
            minb = parameters.get("minb")
            if minb is not None:
                query_filter.append("?b >= %s" % minb)
            maxb = parameters.get("maxb")
            if maxb is not None:
                query_filter.append("?b <= %s" % maxb)
            mine = parameters.get("mine")
            if mine is not None:
                query_filter.append("?e >= %s" % mine)
            maxe = parameters.get("maxe")
            if maxe is not None:
                query_filter.append("?e <= %s" % maxe)
            limit = parameters.get("limit")
            if limit is not None:
                query_epilogue += " LIMIT %s" % limit
            offset = parameters.get("offset")
            if offset is not None:
                query_epilogue += " OFFSET %s" % offset
            if query_filter:
                query_filter = "FILTER(%s)" % (" && ".join(query_filter))
            else:
                query_filter = ""
            query_str = """PREFIX : <http://liris.cnrs.fr/silex/2009/ktbs#>
            SELECT ?obs { ?obs :hasBegin ?b ; :hasEnd ?e . %s } %s
            """ % (query_filter, query_epilogue)

            # add description of all matching obsels
            # TODO LATER include bounded description of obsels
            # rather than just adjacent arcs
            self_state = self.state
            for obs, in self.state.query(query_str): #/!\ returns 1-uples
                get_obsel_bounded_description(obs, self_state, graph)

            return graph


    ######## ILocalCore (and mixins) implementation  ########

    def check_parameters(self, parameters, method):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.check_parameters`

        I also convert parameters values from strings to usable datatypes.
        """
        if parameters is not None \
        and method in ("get_state", "force_state_refresh"):
            for key, val in parameters.items():
                if key in ("minb", "maxb", "mine", "maxe", "limit", "offset"):
                    try:
                        parameters[key] = int(val)
                    except ValueError:
                        raise InvalidParametersError("%s should be an integer"
                                                     "(got %s" % (key, val))
                elif key == "refresh":
                    if val not in _REFRESH_VALUES:
                        raise InvalidParametersError("Invalid value for"
                                                     "'refresh' (%s)" % val)
                elif key == "quick":
                    raise InvalidParameterError("Deprecated parameter 'quick',"
                                                "use refresh=no instead")
                else:
                    raise InvalidParametersError("Unsupported parameters %s"
                                                 % key)
            parameters = None # hide all parameters for super call below
        super(AbstractTraceObsels, self).check_parameters(parameters, method)
    
    def ack_edit(self, parameters, prepared, _query_cache=[None]):
        """I override :meth:`rdfrest.cores.local.ILocalCore.ack_edit`
        to update bookkeeping metadata and force transformed trace to refresh.
        """
        # using lists as default value     #pylint: disable=W0102
        # additional argument _query_cache #pylint: disable=W0221
        super(AbstractTraceObsels, self).ack_edit(parameters, prepared)

        if not self._in_add_graph:
            # find the last obsel and store it in metadata
            query = _query_cache[0]
            if query is None:
                query = _query_cache[0] = prepareQuery("""
                    PREFIX : <http://liris.cnrs.fr/silex/2009/ktbs#>
                    SELECT ?e ?o {
                        ?o :hasEnd ?e .
                        FILTER ( !BOUND(?last_end) || (?e >= ?last_end) )
                    }
                    ORDER BY DESC(?e) LIMIT 1
                """)
            init_bindings = {}
            last_obsel = self.metadata.value(self.uri, METADATA.last_obsel)
            if last_obsel is not None:
                last_end = self.state.value(last_obsel, KTBS.hasEnd)
                # NB: last_end can still be None if last_obsel has been deleted
                if last_end is not None:
                    init_bindings['last_end'] = last_end
            results = list(self.state.query(query, initBindings=init_bindings))
            if results:
                new_last_obsel = results[0][1]
                self.metadata.set((self.uri,
                                   METADATA.last_obsel,
                                   new_last_obsel))
            else:
                new_last_obsel = None
                self.metadata.remove((self.uri,
                                      METADATA.last_obsel,
                                      None))
        else:
            # last_obsel has already been set, more efficiently, by add_graph;
            # we only have to reset self._in_add_graph
            self._in_add_graph = False

        # force transformed traces to refresh
        trace = self.trace
        for ttr in trace.iter_transformed_traces():
            obsels = ttr.obsel_collection
            obsels.metadata.set((obsels.uri, METADATA.dirty, Literal("yes")))

    def delete(self, parameters=None, _trust=False):
        """I override :meth:`.KtbsResource.delete`.

        Obsel collections can not be deleted individually.
        Delete the owning trace instead.
        """
        if _trust:
            # this should only be set of the owning trace
            super(AbstractTraceObsels, self).delete(None, _trust)
        else:
            raise MethodNotAllowedError("Can not delete obsel collection; "
                                        "delete its owning trace instead.")

    # TODO SOON implement check_new_graph on ObselCollection?
    # we should check that the graph only contains well formed obsels

    def iter_etags(self, parameters=None):
        """I override :meth:`rdfrest.cores.mixins.BookkeepingMixin._iter_etags`

        I return self.etag, plus the appropriate monotonicity tag depending
        on the given parameters.
        """
        yield self.etag
        if parameters is not None:
            last_obsel = self.metadata.value(self.uri, METADATA.last_obsel)
            if last_obsel is not None:
                last_end = int(self.state.value(last_obsel, KTBS.hasEnd))
                pse_mon_limit = last_end - self.trace.pseudomon_range
                maxe = parameters.get("maxe")
                if maxe is not None:
                    maxe = int(maxe)
                    if maxe < last_end:
                        yield self.str_mon_tag
                        if maxe < pse_mon_limit:
                            yield self.pse_mon_tag

    ######## Private methods ########

    @classmethod
    def _update_bk_metadata_in(cls, uri, graph):
        """I override
        :meth:`rdfrest.cores.mixins.BookkeepingMixin._update_bk_metadata_in`

        I additionnally generate monotonicity tags.
        """
        super(AbstractTraceObsels, cls)._update_bk_metadata_in(uri, graph)
        token = str(graph.value(uri, RDFREST.etag))
        graph.set((uri, METADATA.str_mon_tag, Literal(token+"s")))
        graph.set((uri, METADATA.pse_mon_tag, Literal(token+"p")))
        graph.set((uri, METADATA.log_mon_tag, Literal(token+"l")))
    
    def _get_new_last_obsel(self, graph, last_obsel):
        """Find the new last obsel once this graph is added.

        Return the obsel URI and its end timestamp.
        """
        if last_obsel is not None:
            last_end = int(self.state.value(last_obsel, KTBS.hasEnd))
        else:
            last_end = None
        for obs, _, end in graph.triples((None, KTBS.hasEnd, None)):
            end = int(end)
            if last_end is None or end > last_end:
                last_end = end
                last_obsel = obs
        return last_obsel, last_end

    def _detect_mon_change(self, graph, old_last_end, pse_mon_limit):
        """Detect monotonicity changed induced by 'graph'.
        
        Note that this is called after graph has been added to self.state,
        so all arcs from graph are also in state.
        """
        str_mon = True
        pse_mon = True
        trace_uri = self.trace.uri
        self_state_value = self.state.value
        # we used a SPARQL query before, but this seems to be more efficient
        for new_obs in graph.subjects(KTBS.hasTrace, trace_uri):
            for obs in chain( [new_obs],
                              graph.objects(new_obs, None),
                              graph.subjects(None, new_obs)):
                end = self_state_value(obs, KTBS.hasEnd)
                if end is None:
                    continue
                end = int(end)
                if end < old_last_end:
                    str_mon = False
                    if end < pse_mon_limit:
                        pse_mon = False
        return str_mon, pse_mon



class StoredTraceObsels(AbstractTraceObsels):
    """I provide the implementation of ktbs:StoredTraceObsels
    """
    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.StoredTraceObsels

class ComputedTraceObsels(AbstractTraceObsels):
    """I provide the implementation of ktbs:ComputedTraceObsels
    """
    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.ComputedTraceObsels

    ######## ICore implementation  ########

    __forcing_state_refresh = False

    def get_state(self, parameters=None):
        """I override `~rdfrest.cores.ICore.get_state`:meth:

        I support parameter 'refresh' to bypass the updating of the obsels,
        or force a recomputation of the trace.
        """
        self.force_state_refresh(parameters)
        return super(ComputedTraceObsels, self).get_state(parameters)

    def force_state_refresh(self, parameters=None):
        """I override `~rdfrest.cores.ICore.force_state_refresh`:meth:

        I recompute the obsels if needed.
        """
        refresh_param = (_REFRESH_VALUES[parameters.get("refresh")]
                         if parameters else 1)
        if refresh_param == 0 or self.__forcing_state_refresh:
            return
        self.__forcing_state_refresh = True
        try:
            LOG.debug("forcing state refresh <%s>", self.uri)
            super(ComputedTraceObsels, self).force_state_refresh(parameters)
            trace = self.trace
            for src in trace.iter_source_traces():
                src.obsel_collection.force_state_refresh(parameters)
            if (self.metadata.value(self.uri, METADATA.dirty, None) is not None
                or refresh_param >= 2):

                LOG.info("recomputing <%s>", self.uri)
                # we *first* unset the dirty bit, so that recursive calls to
                # get_state do not result in an infinite recursion
                self.metadata.remove((self.uri, METADATA.dirty, None))
                trace.force_state_refresh()
                impl = trace._method_impl # friend #pylint: disable=W0212
                diag = impl.compute_obsels(trace, refresh_param >= 2)
                if not diag:
                    self.metadata.set((self.uri, METADATA.dirty,
                                          Literal("yes")))
                    raise CanNotProceedError(unicode(diag))
        finally:
            del self.__forcing_state_refresh


    def edit(self, parameters=None, clear=False, _trust=False):
        """I override :meth:`.KtbsResource.edit`.
        """
        if not _trust:
            raise MethodNotAllowedError(
                "Can not directly edit obsels of computed trace.")
        else:
            return super(ComputedTraceObsels, self).edit(parameters, clear,
                                                         _trust)

    ######## Protected methods ########

    def _empty(self):
        """I remove all obsels from this trace.

        Compared to ``remove(None, None, None)``, this method leaves the
        information about the obsel collection itself.
        """
        with self.edit(_trust=True) as editable:
            trace_uri = editable.value(None, KTBS.hasObselCollection, self.uri)
            editable.remove((None, None, None))
            self.init_graph(editable, self.uri, trace_uri)

_REFRESH_VALUES = {
    "no": 0,
    "default": 1,
    "yes": 2,
    "force": 2,
    "recursive": 3,
    None: 1,
}
