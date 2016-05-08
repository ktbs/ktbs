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

from rdflib import Graph, Literal, RDF
from rdflib.plugins.sparql.processor import prepareQuery

from ktbs.api.resource import KtbsResourceMixin
from rdfrest.cores.mixins import BookkeepingMixin
from rdfrest.exceptions import CanNotProceedError, InvalidParametersError, \
    MethodNotAllowedError
from rdfrest.cores.local import NS as RDFREST, EditableCore
from rdfrest.util import Diagnosis, cache_result
from .resource import METADATA
from .obsel import get_obsel_bounded_description, Obsel
from ..api.trace_obsels import AbstractTraceObselsMixin, _TYPECONV
from ..namespace import KTBS


LOG = getLogger(__name__)

class AbstractTraceObsels(AbstractTraceObselsMixin, KtbsResourceMixin,
                          BookkeepingMixin, EditableCore):
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
        self.check_parameters(parameters, "get_state")
        if parameters is None:
            parameters = {}

        query_str = self._make_obsel_query(parameters)

        graph = Graph(identifier=self.uri)
        graph_add = graph.add

        # fill graph with data about the obsel collection
        for triple in self._graph.triples((self.uri, None, None)):
            graph_add(triple)
        for triple in self._graph.triples((None, None, self.uri)):
            graph_add(triple)

        # TODO LATER use a DESCRIBE query above,
        # in order to generate the whole graph in one query?
        # (rather than with the loop below)
        # NB: DESCRIBE is currently not implemented currently in rdflib

        # add description of all matching obsels
        obs = None
        store = self.service.store
        for obs, in self.service.query(query_str): #/!\ returns 1-uples
            get_obsel_bounded_description(obs, Graph(store, obs), graph)

        # generate 'next' link
        if 'limit' in parameters and obs:
            obs_id = obs.rsplit("/", 1)[1]
            if 'reverse' in parameters:
                qstr = "?reverse&limit=%s&before=%s"\
                       % (parameters['limit'], obs_id)
            else:
                qstr = "?limit=%s&after=%s" % (parameters['limit'], obs_id)
            if 'minb' in parameters:
                qstr += "&minb=%s" % parameters['minb']
            if 'maxb' in parameters:
                qstr += "&maxb=%s" % parameters['maxb']
            if 'mine' in parameters:
                qstr += "&mine=%s" % parameters['mine']
            if 'maxe' in parameters:
                qstr += "&maxe=%s" % parameters['maxe']
            graph.next_link = self.uri + qstr

        return graph

    def edit(self, parameters=None, clear=False, _trust=False):
        """I override :meth:`.KtbsResource.edit`.
        """
        if not _trust:
            raise MethodNotAllowedError(
                "Can not directly edit obsel collection. "
                "Edit individual obsels instead."
            )
        else:
            return super(AbstractTraceObsels, self).edit(parameters, clear,
                                                         _trust)

    def delete(self, parameters=None, _trust=False):
        """I override :meth:`.KtbsResource.delete`.

        Deleting an obsel collection also deletes all the obsels.
        """
        # NB: for performance reasons, obsels are not deleted with Obsel.delete,
        # but with a single SPARUL query to the triple store
        if _trust: # this should only be set by the owning trace
            self._empty()
            super(AbstractTraceObsels, self).delete(parameters, _trust)
        else:
            raise MethodNotAllowedError(
                "Can not delete obsel collection directly. "
                "Delete the owning trace instead."
            )


    ######## ILocalCore (and mixins) implementation  ########

    def check_parameters(self, parameters, method):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.check_parameters`

        I also convert parameters values from strings to usable datatypes.
        """
        if parameters is not None:
            if method in ("get_state", "force_state_refresh"):
                for key, val in parameters.items():
                    if key in ("minb", "maxb", "mine", "maxe", "limit", "offset"):
                        try:
                            parameters[key] = int(val)
                        except ValueError:
                            raise InvalidParametersError(
                                "%s should be an integer (got %s" % (key, val))
                    elif key == "refresh":
                        if val not in _REFRESH_VALUES:
                            raise InvalidParametersError(
                                "Invalid value for 'refresh' (%s)" % val)
                    elif key == "quick":
                        raise InvalidParametersError(
                            "Deprecated parameter 'quick', "
                            "use refresh=no instead")
                    elif key in ("after", "before"):
                        parameters[key] = obs = self.trace.get_obsel(val)
                        try:
                            begin = obs.begin
                        except TypeError, AttributeError:
                            obs = None
                        if obs is None:
                            raise InvalidParametersError(
                                "%s should be an existing obsel"
                                "(got %s)" % (key, val))
                    elif key in ("reverse", "bgp"):
                        pass
                    else:
                        raise InvalidParametersError("Unsupported parameters %s"
                                                     % key)
                parameters = None # hide all parameters for super call below
            elif method in ("edit"):
                for key, val in parameters.items():
                    if key == "add_obsels_only":
                        pass
                    else:
                        raise InvalidParametersError("Unsupported parameters %s"
                                                     % key)
                parameters = None # hide all parameters for super call below
        super(AbstractTraceObsels, self).check_parameters(parameters, method)

    def prepare_edit(self, parameters):
        """I overrides :meth:`rdfrest.cores.local.ILocalCore.prepare_edit`

        I store old values related to monotonicity.
        change in :meth:`ack_edit`.
        """
        ret = super(AbstractTraceObsels, self).prepare_edit(parameters)
        ret.last_obsel = obs_uri = self.metadata.value(self.uri, METADATA.last_obsel)
        if obs_uri is not None:
            res = self.service.query(FIND_BEGIN_END,
                                     initBindings={'obs': obs_uri})
            blit, elit = next(iter(res))
            ret.last_begin = int(blit)
            ret.last_end = int(elit)
        ret.str_mon = ret.pse_mon = ret.log_mon = (
            parameters and "add_obsels_only" in parameters)
        return ret

    def ack_edit(self, parameters, prepared):
        """I override :meth:`rdfrest.cores.local.ILocalCore.ack_edit`
        to update bookkeeping metadata and force transformed trace to refresh.
        """
        # using lists as default value     #pylint: disable=W0102
        # additional argument _query_cache #pylint: disable=W0221
        super(AbstractTraceObsels, self).ack_edit(parameters, prepared)

        trace = self.trace

        # find the last obsel and store it in metadata
        if parameters and "add_obsels_only" in parameters:
            new_last_obsel = prepared.last_obsel
        else:
            init_bindings = {'trace': trace.uri, 'self': self.uri}
            last_obsel = prepared.last_obsel
            if last_obsel is not None:
                log = Graph(self.service.store, last_obsel)
                last_end = log.value(last_obsel, KTBS.hasEnd)
                # NB: last_end can still be None if last_obsel has been deleted
                if last_end is not None:
                    init_bindings['last_end'] = Literal(prepared.last_end)
            results = list(self.service.query(FIND_LAST_OBSEL,
                                              initBindings=init_bindings))
            if results:
                new_last_obsel = results[0][0]
            else:
                new_last_obsel = None

        LOG.debug('ack_edit: set last_obsel: %s', new_last_obsel)
        if new_last_obsel is not None:
            self.metadata.set((self.uri, METADATA.last_obsel, new_last_obsel))
        else:
            self.metadata.remove((self.uri, METADATA.last_obsel, None))

        # force transformed traces to refresh
        for ttr in trace.iter_transformed_traces():
            obsels = ttr.obsel_collection
            obsels.metadata.set((obsels.uri, METADATA.dirty, Literal("yes")))


    def iter_etags(self, parameters=None):
        """I override :meth:`rdfrest.cores.mixins.BookkeepingMixin._iter_etags`

        I return self.etag, plus the appropriate monotonicity tag depending
        on the given parameters.
        """
        yield self.etag
        if parameters is not None:
            last_obsel = self.metadata.value(self.uri, METADATA.last_obsel)
            if last_obsel is not None:
                last_end_result = self.service.query(
                    'SELECT ?end { GRAPH ?o { ?o :hasEnd ?end } }',
                    initNs={'': KTBS},
                    initBindings={'o': last_obsel},
                )
                last_end = int(next(iter(last_end_result))[0])
                pse_mon_limit = last_end - self.trace.pseudomon_range
                maxe = parameters.get("maxe")
                if maxe is not None:
                    maxe = int(maxe)
                    if maxe < last_end:
                        yield self.str_mon_tag
                        if maxe < pse_mon_limit:
                            yield self.pse_mon_tag

    ######## Optimization  ########

    @property
    @cache_result
    def trace_uri(self):
        """This is an optimization of `ktbs.api.trace_obsels.AbstractTraceObselsMixin.trace_uri`:meth:
        """
        graph = self._graph
        return graph.value(None, KTBS.hasObselCollection, self.uri)

    @property
    @cache_result
    def trace(self):
        """This is an optimization of `ktbs.api.trace_obsels.AbstractTraceObselsMixin.trace`:meth:
        """
        graph = self._graph
        trace_uri = graph.value(None, KTBS.hasObselCollection, self.uri)
        self_type = graph.value(self.uri, RDF.type)
        trace_type = _TYPECONV[self_type]
        return self.factory(trace_uri, [trace_type])
        # must be a .trace.AbstractTraceMixin

    @property
    def state(self):
        raise NotImplementedError(
            "property 'state' no more supported for ObselCollection, "
            "use get_state() instead"
        )

    ######## Protected methods ########

    def _make_obsel_query (self, parameters=None, select_clause="SELECT ?obs"):
        """I make the query for all obsels
        """
        query_filter = []
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
        after = parameters.get("after")
        if after is not None:
            query_filter.append(
                "?e > {2} || "
                "?e = {2} && ?b > {1} || "
                "?e = {2} && ?b = {1} && str(?obs) > \"{0}\"".format(
                    after.uri, after.begin, after.end,
                ))
        before = parameters.get("before")
        if before is not None:
            query_filter.append(
                "?e < {2} || "
                "?e = {2} && ?b < {1} || "
                "?e = {2} && ?b = {1} && str(?obs) < \"{0}\"".format(
                    before.uri, before.begin, before.end
                ))
        if query_filter:
            query_filter = "FILTER((%s))" % (") && (".join(query_filter))
        else:
            query_filter = ""

        query_epilogue = ""
        reverse = (parameters.get("reverse", "no").lower()
                   not in ("false", "no", "0"))
        if reverse:
            query_epilogue += "ORDER BY DESC(?e) DESC(?b) DESC(?obs)"
        else:
            query_epilogue += "ORDER BY ?e ?b ?obs"
        limit = parameters.get("limit")
        if limit is not None:
            query_epilogue += " LIMIT %s" % limit
        offset = parameters.get("offset")
        if offset is not None:
            query_epilogue += " OFFSET %s" % offset

        trace = self.trace

        query_str = """
        PREFIX : <http://liris.cnrs.fr/silex/2009/ktbs#>
        PREFIX m: <%s>
        %s {
            GRAPH <%s> { ?obs :hasTrace <%s> }
            GRAPH ?obs { ?obs :hasBegin ?b ; :hasEnd ?e }
            %s
            %s
        } %s
        """ % (trace.model_prefix, select_clause, self.uri, trace.uri,
               parameters.get('bgp', ""),query_filter,
               query_epilogue)

        LOG.debug("_make_obsel_query: %s", query_str)
        return query_str


    def _add_obsel(self, obsel_uri, graph, create_it=True):
        """Add the obsel to this obsel collection.

        :param obsel_uri: the URI of the new obsel
        :type obsel_uri: rdflib.URIRef
        :param graph: the graph describing this obsel
        :type graph: rdflib.graph.Graph
        :param create_it: whether the obsel must be created in the store
        :type create_it: bool

        If you need to add only one obsel,
        you can use this method *without* using any `~rdfrest.cores.ICore.edit`:meth: context.

        If you need to call this method multiple time,
        it is more efficient to wrap all the calls to ``_add_obsel``
        inside a single `~rdfrest.cores.ICore.edit`:meth: context,
        which then *must* have the ``add_obsels_only`` parameter set.

        This should be used instead of the
        `~rdfrest.cores.ICore.edit`:meth: context when no arc has to
        be removed, as it will not change the
        `log_mon_tag`:meth`.
        """
        LOG.debug('_add_obsel: %s %s', obsel_uri, create_it)
        assert self._edit_context is None  or  self._edit_context[0], \
            "No point in calling _add_obsel inside an untrusted edit context"

        if create_it:
            Obsel.create(self.service, obsel_uri, graph)

        with self.edit({"add_obsels_only": 1}, _trust=True) \
        as editable:
            prepared = self._edit_context[2]
            editable.add((obsel_uri, KTBS.hasTrace, self.trace_uri))
            self._detect_mon_change(obsel_uri, graph, self.trace_uri, prepared)


    def _empty(self):
        """I remove all obsels from this trace.

        # NB: for performance reasons, obsels are not deleted with Obsel.delete,
        # but by directly erasing them from the underlying store.
        """
        with self.edit(_trust=True):
            self.service.update("""
                DELETE {
                    GRAPH ?self { ?obs :hasTrace ?trace }
                    GRAPH ?obs { ?s ?p ?o }
                }
                WHERE {
                    GRAPH ?self { ?obs :hasTrace ?trace }
                    GRAPH ?obs { ?s ?p ?o }
                }
                """,
                initNs = {'': KTBS},
                initBindings={'self': self.uri},
            )

    ######## Private methods ########

    @classmethod
    def _update_bk_metadata_in(cls, uri, graph, prepared=None):
        """I override
        :meth:`rdfrest.cores.mixins.BookkeepingMixin._update_bk_metadata_in`

        I additionnally generate monotonicity tags.
        """
        super(AbstractTraceObsels, cls)._update_bk_metadata_in(uri, graph)
        token = str(graph.value(uri, RDFREST.etag))
        if prepared is None  or   not prepared.str_mon:
            graph.set((uri, METADATA.str_mon_tag, Literal(token+"s")))
        if prepared is None  or  not prepared.pse_mon:
            graph.set((uri, METADATA.pse_mon_tag, Literal(token+"p")))
        if prepared is None  or  not prepared.log_mon:
            graph.set((uri, METADATA.log_mon_tag, Literal(token+"l")))
    
    def _detect_mon_change(self, new_obs, graph, trace_uri, prepared):
        """Detect monotonicity changed induced by 'obsel_uri',
        and update `prepared` accordingly.
        
        Note that this is called after graph has been added to self._graph,
        so all arcs from graph are also in state.
        """
        if prepared.last_obsel is None:
            prepared.last_obsel = new_obs
            prepared.last_begin = int(graph.value(new_obs, KTBS.hasBegin))
            prepared.last_end = int(graph.value(new_obs, KTBS.hasEnd))-1
            return

        old_last_obsel = prepared.last_obsel
        old_last_begin = prepared.last_begin
        old_last_end = prepared.last_end
        pseudomon_range = self.trace.pseudomon_range
        pse_mon_b_limit = old_last_begin - pseudomon_range
        pse_mon_e_limit = old_last_end - pseudomon_range

        str_mon = True
        pse_mon = True

        end = int(graph.value(new_obs, KTBS.hasEnd))
        begin = None
        if end < old_last_end:
            str_mon = False
            if end < pse_mon_e_limit:
                pse_mon = False
        elif end == old_last_end:
            begin = int(graph.value(new_obs, KTBS.hasBegin))
            if begin < old_last_begin:
                str_mon = False
                if begin < pse_mon_b_limit:
                    pse_mon = False
            elif begin == old_last_begin:
                if new_obs <= old_last_obsel:
                    str_mon = False
        if str_mon:
            prepared.last_obsel = new_obs
            if begin is None:
                begin = int(graph.value(new_obs, KTBS.hasBegin))
            prepared.last_begin = begin
            prepared.last_end = end

        prepared.str_mon = prepared.str_mon and str_mon
        prepared.pse_mon = prepared.pse_mon and pse_mon



class StoredTraceObsels(AbstractTraceObsels):
    """I provide the implementation of ktbs:StoredTraceObsels
    """
    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.StoredTraceObsels

    ######## ICore implementation  ########

    def delete(self, parameters=None, _trust=False):
        """I override :meth:`AbstractTraceObsels.delete`.

        If untrusted, delete the obsels, but not the obsel collection itself.
        """
        if not _trust:
            self.check_parameters(parameters, "delete")
            self._empty()
        else:
            super(StoredTraceObsels, self).delete(parameters, _trust)


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
                try:
                    diag = impl.compute_obsels(trace, refresh_param >= 2)
                except BaseException, ex:
                    diag = Diagnosis(
                        "exception raised while computing obsels",
                        ["{}: {}".format(type(ex).__name__, ex.message)]
                    )
                if not diag:
                    self.metadata.set((self.uri, METADATA.dirty,
                                          Literal("yes")))
                    raise CanNotProceedError(unicode(diag))
        finally:
            del self.__forcing_state_refresh



FIND_BEGIN_END = prepareQuery("""
    SELECT ?b ?e {
        GRAPH ?obs { ?obs :hasBegin ?b ; :hasEnd ?e }
    }
""", initNs = {'': KTBS})

FIND_LAST_OBSEL = prepareQuery("""
    SELECT ?o {
        GRAPH ?self { ?o :hasTrace ?trace }
        GRAPH ?o { ?o :hasEnd ?e }
        FILTER ( !BOUND(?last_end) || (?e >= ?last_end) )
    }
    ORDER BY DESC(?e) LIMIT 1
""", initNs = {'': KTBS})


_REFRESH_VALUES = {
    "no": 0,
    "default": 1,
    "yes": 2,
    "force": 2,
    "recursive": 3,
    None: 1,
}
