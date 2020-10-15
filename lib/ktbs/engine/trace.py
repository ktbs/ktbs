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
I provide the implementation of ktbs:StoredTrace and ktbs:ComputedTrace .
"""
import traceback
from datetime import datetime
from logging import getLogger

from rdflib import BNode, Graph, Literal, URIRef, XSD
from rdflib.plugins.sparql.processor import prepareQuery

from ktbs.engine.trace_stats import TraceStatistics
from ktbs.time import lit2datetime, get_converter_to_unit
from rdfrest.exceptions import InvalidDataError
from rdfrest.cores.factory import factory as universal_factory
from rdfrest.cores.local import compute_added_and_removed
from rdfrest.cores.mixins import FolderishMixin
from rdfrest.util import bounded_description, cache_result, random_token, replace_node_sparse, \
    Diagnosis
from .base import InBase
from .builtin_method import get_builtin_method_impl
from .obsel import Obsel
from .resource import KtbsPostableMixin, METADATA
from .trace_obsels import ComputedTraceObsels, StoredTraceObsels
from ..api.trace import AbstractTraceMixin, StoredTraceMixin, ComputedTraceMixin
from ..namespace import KTBS, KTBS_NS_URI
from ..utils import extend_api, check_new


LOG = getLogger(__name__)

@extend_api
class AbstractTrace(AbstractTraceMixin, InBase):
    """I provide the implementation of ktbs:AbstractTrace .
    """

    def __iter__(self):
        return self.iter_obsels()

    ######## Extension to the abstract kTBS API  ########
    # (only available on *local* objects)

    @property
    def unit(self):
        """I return this trace's time unit.

        I get it from the model if available, and store it in the trace's
        metadata in case the model is not available.
        """
        try:
            unit = self.get_model().unit
            self.metadata.set((self.uri, METADATA.unit, unit))
        except BaseException:
            unit = self.metadata.value(self.uri, METADATA.unit) \
                or KTBS.millisecond
        return unit

    @property
    @cache_result
    def obsel_collection(self):
        """I override :attr:`..api.trace.AbstractTrace.obsel_collection`.

        Instead of an OpportunisticObselCollection, I return the actual
        resource, as there is no need to optimize transfer in a local
        implementation.
        """
        obsels_uri = self.state.value(self.uri, KTBS.hasObselCollection)
        return self.service.get(obsels_uri, [self._obsels_cls.RDF_MAIN_TYPE])


    ######## ILocalCore (and mixins) implementation  ########

    @classmethod
    def check_new_graph(cls, service, uri, parameters, new_graph,
                        resource=None, added=None, removed=None):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.check_new_graph`

        I check that the sources exist and are in the same base.
        """
        diag = super(AbstractTrace, cls).check_new_graph(
            service, uri, parameters, new_graph, resource, added, removed)

        if resource is not None:
            old_graph = resource.get_state()
            added, removed = compute_added_and_removed(new_graph, old_graph,
                                                       added, removed)
            src_graph = added
        else:
            src_graph = new_graph

        base_uri = new_graph.value(None, KTBS.contains, uri)
        factory = service.get
        for src_uri in src_graph.objects(uri, KTBS.hasSource):
            if not src_uri.startswith(base_uri) \
            or not isinstance(factory(src_uri), AbstractTrace):
                diag.append("Source <%s> is not a trace from the same base"
                            % src_uri)

        return diag

    @classmethod
    def create(cls, service, uri, new_graph):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.create`

        I create the obsel collection and the statistics resource associated with this trace,
        and I notify this trace's sources.
        """
        super(AbstractTrace, cls).create(service, uri, new_graph)

        # create obsel collection
        obsels_uri = URIRef(uri + "@obsels")
        graph = Graph(service.store, uri)
        graph.add((uri, KTBS.hasObselCollection, obsels_uri))
        obsels_graph = Graph(identifier=obsels_uri)
        cls._obsels_cls.init_graph(obsels_graph, obsels_uri, uri)
        cls._obsels_cls.create(service, obsels_uri, obsels_graph)

        # create trace statistics
        stats_uri = URIRef(uri + "@stats")
        graph.add((uri, KTBS.hasTraceStatistics, stats_uri))
        stats_graph = Graph(identifier=stats_uri)
        TraceStatistics.init_graph(stats_graph, stats_uri, uri)
        TraceStatistics.create(service, stats_uri, stats_graph)

        # notify sources
        sources = list(new_graph.objects(uri, KTBS.hasSource))
        cls._notify_sources(service, uri, sources)

    def prepare_edit(self, parameters):
        """I overrides :meth:`rdfrest.cores.local.ILocalCore.prepare_edit`

        I store old values of some properties (sources, pseudomon range)
        to handle the change in :meth:`ack_edit`.
        """
        ret = super(AbstractTrace, self).prepare_edit(parameters)
        ret.old_pseudomon_range = self.get_pseudomon_range()
        ret.old_sources = set(self.state.objects(self.uri, KTBS.hasSource))
        return ret

    def ack_edit(self, parameters, prepared):
        """I overrides :meth:`rdfrest.cores.local.ILocalCore.ack_edit`

        I reflect changes in the related resources (sources, obsel collection).
        """
        super(AbstractTrace, self).ack_edit(parameters, prepared)
        # manage changes in pseudo-monotonicity range
        if self.get_pseudomon_range() > prepared.old_pseudomon_range:
            with self.obsel_collection.edit(_trust=True):
                pass # just force renewal of all tags
        # manage changes in sources
        new_sources = set(self.state.objects(self.uri, KTBS.hasSource))
        if new_sources != prepared.old_sources:
            self._ack_source_change(prepared.old_sources, new_sources)
        for ttr in self.iter_transformed_traces():
            ttr._mark_dirty()

    def check_deletable(self, parameters):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.check_deletable`

        I refuse to be deleted if I am the source of another trace.
        """
        diag = super(AbstractTrace, self).check_deletable(parameters)
        for i in self.iter_transformed_traces():
            diag.append("<%s> is used (ktbs:hasSource) by <%s>"
                        % (self.uri, i.uri))
        return diag

    def ack_delete(self, parameters):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.ack_delete`
        """
        old_traces = self.state.objects(self.uri, KTBS.hasSource)
        self._ack_source_change(old_traces, [])
        self.obsel_collection.delete(_trust=True)
        if self.trace_statistics:
            # Traces created before @stats was introduced have no trace_statistics
            self.trace_statistics.delete(_trust=True)
        super(AbstractTrace, self).ack_delete(parameters)


    ######## Private methods  ########

    def _ack_source_change(self, old_source_uris, new_source_uris):
        """I record the fact that my sources have changed
        """
        self._notify_sources(self.service, self.uri, new_source_uris,
                             old_source_uris)

    @classmethod
    def _notify_sources(cls, service, uri, new_source_uris, old_source_uris=()):
        """I inform sources that they are (or are no longer) sources of uri.
        """
        factory = service.get
        for old in old_source_uris:
            with factory(old).edit(_trust=True) as editable:
                editable.remove((uri, KTBS.hasSource, old))
        for new in new_source_uris:
            with factory(new).edit(_trust=True) as editable:
                editable.add((uri, KTBS.hasSource, new))


class StoredTrace(StoredTraceMixin, KtbsPostableMixin, AbstractTrace):
    """I provide the implementation of ktbs:StoredTrace .
    """

    _obsels_cls = StoredTraceObsels

    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.StoredTrace

    RDF_EDITABLE_OUT =    [ KTBS.hasModel, KTBS.hasOrigin, KTBS.hasTraceBegin,
                            KTBS.hasTraceEnd, KTBS.hasTraceBeginDT,
                            KTBS.hasTraceEndDT, KTBS.hasDefaultSubject,
                            KTBS.hasPseudoMonRange, KTBS.hasContext,
                            ]
    RDF_CARDINALITY_OUT = [ (KTBS.hasModel, 1, 1),
                            (KTBS.hasOrigin, 1, 1),
                            (KTBS.hasTraceBegin, None, 1),
                            (KTBS.hasTraceBeginDT, None, 1),
                            (KTBS.hasTraceEnd, None, 1),
                            (KTBS.hasTraceEndDT, None, 1),
                            (KTBS.hasDefaultSubject, None, 1),
                            (KTBS.hasPseudoMonRange, 0, 1),
                            ]
    RDF_TYPED_PROP =      [ (KTBS.hasModel,          "uri"),
                            (KTBS.hasOrigin,         "literal"),
                            (KTBS.hasTraceBegin,     "literal", XSD.integer),
                            (KTBS.hasTraceBeginDT,   "literal", XSD.dateTime),
                            (KTBS.hasTraceEnd,       "literal", XSD.integer),
                            (KTBS.hasTraceEndDT,     "literal", XSD.dateTime),
                            (KTBS.hasPseudoMonRange, "literal", XSD.integer),
                            (KTBS.hasContext,        "uri"),
                            ]

    @classmethod
    def check_new_graph(cls, service, uri, parameters, new_graph,
                        resource=None, added=None, removed=None):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.check_new_graph`

        I check the temporal extension of this trace.
        """
        # if resource is not None:
        #     old_graph = resource.get_state()
        #     added, removed = compute_added_and_removed(new_graph, old_graph,
        #                                                added, removed)
        diag = super(StoredTrace, cls).check_new_graph(
            service, uri, parameters, new_graph, resource, added, removed)

        # TODO LATER check consistency of trace extension
        # note however that we may deprecate those propeties in favor of
        # origin/duration

        return diag

    @classmethod
    def complete_new_graph(cls, service, uri, parameters, new_graph,
                           resource=None):
        """I implement :meth:`ILocalCore.complete_new_graph`.

        At create time, I add default values for missing information about the
        trace.
        """
        super(StoredTrace, cls).complete_new_graph(service, uri, parameters,
                                                   new_graph, resource)
        if resource is None:
            origin = new_graph.value(uri, KTBS.hasOrigin)
            if origin is None:
                origin = Literal("o"+random_token(32))
                # start origin with a letter because if it starts with 4 digits,
                # it will be misinterpreted for a year
                new_graph.add((uri, KTBS.hasOrigin, origin))
            elif str(origin) == "now":
                origin = Literal("%sZ" % datetime.utcnow().isoformat())
                new_graph.set((uri, KTBS.hasOrigin, origin))


        # compute begin and/or end if beginDT and/or endDT are provided
        begin_dt = lit2datetime(new_graph.value(uri, KTBS.hasTraceBeginDT))
        end_dt = lit2datetime(new_graph.value(uri, KTBS.hasTraceEndDT))
        if begin_dt or end_dt:
            model = universal_factory(new_graph.value(uri, KTBS.hasModel),
                                      [KTBS.TraceModel])
            delta2unit = get_converter_to_unit(model.unit)
            origin = lit2datetime(new_graph.value(uri, KTBS.hasOrigin))
            if origin is not None:
                if delta2unit is not None:
                    if begin_dt is not None:
                        begin = delta2unit(begin_dt - origin)
                        new_graph.add((uri, KTBS.hasTraceBegin, Literal(begin)))
                    if end_dt is not None:
                        end = delta2unit(end_dt - origin)
                        new_graph.add((uri, KTBS.hasTraceEnd, Literal(end)))


    def check_new(self, created):
        """ I override :meth:`GraphPostableMixin.check_new`.

        I check if the created resource exists in my obsel collection.
        """
        return check_new(self.obsel_collection.get_state(), created)

    def post_graph(self, graph, parameters=None,
                   _trust=False, _created=None, _rdf_type=None):
        """I override :meth:`rdfrest.util.GraphPostableMixin.post_graph`.

        I allow for multiple obsels to be posted at the same time.
        """
        base = self.get_base()
        post_single_obsel = super(StoredTrace, self).post_graph
        binding = { "trace": self.uri }
        ret = []
        candidates = [ i[0] for i in graph.query(_SELECT_CANDIDATE_OBSELS,
                                                 initBindings=binding) ]
        bnode_candidates = { i for i in candidates
                               if isinstance(i, BNode) }
        with self.obsel_collection.edit({"add_obsels_only":1}, _trust=True):
            for candidate in candidates:
                if isinstance(candidate, BNode):
                    bnode_candidates.remove(candidate)
                obs_graph = bounded_description(candidate, graph, prune=bnode_candidates)
                for other in bnode_candidates:
                    obs_graph.remove((candidate, None, other))
                    obs_graph.remove((other, None, candidate))

                ret1 = post_single_obsel(obs_graph, parameters, _trust, candidate,
                                         KTBS.Obsel)
                if ret1:
                    assert len(ret1) == 1
                    new_obs = ret1[0]
                    ret.append(new_obs)
                    if new_obs != candidate:
                        replace_node_sparse(graph, candidate, new_obs)

        assert not bnode_candidates, bnode_candidates
        if not ret:
            raise InvalidDataError("No obsel found in posted graph")

        stats = self.trace_statistics
        if stats:
            # Traces created before @stats was introduced have no trace_statistics
            stats.metadata.set((stats.uri, METADATA.dirty, YES))
        return ret

    def get_created_class(self, rdf_type):
        """I override
        :class:`rdfrest.cores.mixins.GraphPostableMixin.get_created_class`
        Only obsels can be posted to a trace.
        """
        # unused arguments #pylint: disable=W0613
        # self is not used #pylint: disable=R0201
        return Obsel

# the following query gets all the candidate obsels in a POSTed graph,
# and orders them correctly, guessing implicit values
_SELECT_CANDIDATE_OBSELS = prepareQuery("""
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX : <%s#>
    SELECT ?obs
           (IF(bound(?b), ?b, "INF"^^xsd:float) as ?begin)
           (IF(bound(?e), ?e, ?begin) as ?end)
           $trace # selected solely to please Virtuoso
    WHERE {
        ?obs :hasTrace ?trace
        OPTIONAL { ?obs :hasBegin ?b }
        OPTIONAL { ?obs :hasEnd   ?e }
    }
    ORDER BY ?begin ?end
""" % KTBS_NS_URI)


class ComputedTrace(ComputedTraceMixin, FolderishMixin, AbstractTrace):
    """I provide the implementation of ktbs:ComputedTrace .
    """

    _obsels_cls = ComputedTraceObsels

    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.ComputedTrace

    RDF_EDITABLE_OUT =    [ KTBS.hasMethod,
                            KTBS.hasParameter,
                            KTBS.hasSource,
                            ]
    RDF_CARDINALITY_OUT = [ (KTBS.hasMethod, 1, 1),
                            ]
    RDF_TYPED_PROP =      [ (KTBS.hasParentMethod, "uri"),
                            (KTBS.hasParameter, "literal"),
                            (KTBS.hasSource,       "uri"),
                            ]

    @classmethod
    def create(cls, service, uri, new_graph):
        """I implement :meth:`AbstractTrace.create`

        I notify this trace's method, and I ensure that it is run once to
        compute the computed properties (model, origin) of this trace.
        """
        super(ComputedTrace, cls).create(service, uri, new_graph)
        created = service.get(uri)
        assert isinstance(created, ComputedTrace)
        created._mark_dirty() # friend #pylint: disable=W0212
        created.force_state_refresh()
        method = created.method
        if getattr(method, "service", None) is service:
            with method.edit(_trust=True) as editable:
                editable.add((uri, KTBS.hasMethod, method.uri))

    def prepare_edit(self, parameters):
        """I overrides :meth:`rdfrest.cores.local.ILocalCore.prepare_edit`

        I store old values of some properties (parameters, method) to handle the
        change in :meth:`ack_edit`.
        """
        ret = super(ComputedTrace, self).prepare_edit(parameters)
        ret.old_params = set(self.state.objects(self.uri, KTBS.hasParameter))
        ret.old_method = self.state.value(self.uri, KTBS.hasMethod)
        return ret

    def ack_edit(self, parameters, prepared):
        """I overrides :meth:`rdfrest.cores.local.ILocalCore.ack_edit`

        I reflect changes in the related resources (method, obsel collection).
        """
        super(ComputedTrace, self).ack_edit(parameters, prepared)
        new_method = self.state.value(self.uri, KTBS.hasMethod)
        if prepared.old_method != new_method:
            self._ack_method_change(prepared.old_method, new_method)
        new_params = set(self.state.objects(self.uri, KTBS.hasParameter))
        if prepared.old_params != new_params:
            self._mark_dirty()

    def ack_delete(self, parameters):
        """I override :meth:`~rdfrest.cores.local.EditableCore.ack_delete`

        I notify my method that I'm no longer using it.
        """
        method_uri = self.state.value(self.uri, KTBS.hasMethod)
        self._ack_method_change(method_uri, None)
        super(ComputedTrace, self).ack_delete(parameters)


    ######## ICore implementation  ########

    __forcing_state_refresh = False

    def get_state(self, parameters=None):
        """I override `~rdfrest.cores.ICore.get_state`:meth:

        I systematically call :meth:`force_state_refresh` to ensure all
        computations have been performed.
        """
        self.force_state_refresh(parameters)
        return super(ComputedTrace, self).get_state(parameters)

    def force_state_refresh(self, parameters=None):
        """I override `~rdfrest.cores.ICore.force_state_refresh`:meth:

        I recompute my data if needed.
        """
        if self.__forcing_state_refresh:
            return
        self.__forcing_state_refresh = True
        try:
            super(ComputedTrace, self).force_state_refresh(parameters)
            for src in self._iter_effective_source_traces():
                src.force_state_refresh(parameters)
            if self.metadata.value(self.uri, METADATA.dirty, None) is not None:
                # we *first* unset the dirty bit, so that recursive calls to
                # get_state do not result in an infinite recursion
                self.metadata.remove((self.uri, METADATA.dirty, None))
                with self.edit(_trust=True) as editable:
                    editable.remove((self.uri, KTBS.hasDiagnosis, None))
                    editable.remove((self.uri, KTBS.hasModel, None))
                    editable.remove((self.uri, KTBS.hasOrigin, None))
                    try:
                        diag = self._method_impl.compute_trace_description(self)
                    except BaseException as ex:
                        LOG.warning(traceback.format_exc())
                        diag = Diagnosis(
                            "exception raised while computing trace description",
                            [ex.args[0]]
                        )
                    if not diag:
                        editable.add((self.uri, KTBS.hasDiagnosis,
                                         Literal(str(diag))))
                for ttr in self.iter_transformed_traces():
                    ttr._mark_dirty()
        finally:
            del self.__forcing_state_refresh


    ######## Protected method  ########

    def _iter_effective_source_traces(self):
        """I iter over the effective sources of this computed trace.

        The effective sources are usually the declared sources,
        except for composite methods (pipe, parallel),
        that store alternative effective sources in the metadata.
        """
        eff_src_uris = list(
            self.metadata.objects(self.uri, METADATA.effective_source)
        )
        if eff_src_uris:
            return (self.factory(uri) for uri in eff_src_uris)
        else:
            return self.iter_source_traces()

    ######## Private method  ########

    def _ack_source_change(self, old_source_uris, new_source_uris):
        """I override :meth:`AbstractTrace._ack_source_change`

        I force my obsel collection to be recomputed.
        """
        super(ComputedTrace, self)._ack_source_change(old_source_uris,
                                                      new_source_uris)
        self._mark_dirty()

    def _ack_method_change(self, old_method_uri, new_method_uri):
        """I acknowledge a change of method.

        I notify my old and my new method of the change;
        """
        old_method = self.service.get(old_method_uri)
        if old_method is not None: # it is not a built-in method
            with old_method.edit(_trust=True) as editable:
                editable.remove((self.uri, KTBS.hasMethod, old_method_uri))
        if new_method_uri is not None:
            new_method = self.service.get(new_method_uri)
            if new_method is not None: # it is not a built-in method
                with new_method.edit(_trust=True) as editable:
                    editable.add((self.uri, KTBS.hasMethod, new_method_uri))
        self.__method_impl = None
        self._mark_dirty()

    def _mark_dirty(self, metadata=True, obsels=True):
        """Notify me that my source(s) have changed.

        Note that the resulting recomputation will only occur when my state
        (or the state of my obsel collection) is required.
        """
        if metadata:
            self.metadata.add((self.uri, METADATA.dirty, YES))
        if obsels:
            obsels = self.obsel_collection
            obsels.metadata.add((obsels.uri, METADATA.dirty, YES))

    __method_impl = None
    # do NOT use @cache_result here, as the result may change over time

    @property
    def _method_impl(self):
        """I hold the python object implementing my method.
        """
        if self.__method_impl is None:
            uri = self.get_method_uri()
            ret = get_builtin_method_impl(uri)

            while ret is None:
                met = universal_factory(uri, [KTBS.Method])
                try:
                    parent_uri = getattr(met, "parent_uri", None)
                except:
                    parent_uri = None
                if parent_uri:
                    uri = parent_uri
                    ret = get_builtin_method_impl(uri)
                else:
                    ret = get_builtin_method_impl(uri, True)
                    # the above will always return a method (possibly fake)
                    # so we will exit the loop
            self.__method_impl = ret
        else:
            ret = self.__method_impl
        return ret

YES = Literal('yes')
