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
from logging import getLogger

from rdflib import Graph, Literal, URIRef, XSD
from rdflib.plugins.sparql.processor import prepareQuery

from rdfrest.exceptions import InvalidDataError
from rdfrest.cores.local import compute_added_and_removed
from rdfrest.cores.mixins import FolderishMixin
from rdfrest.util import cache_result, random_token
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
        return self.service.get(obsels_uri)


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

        I create the obsel collection associated with this trace,
        and I notify this trace's sources.
        """
        super(AbstractTrace, cls).create(service, uri, new_graph)

        # create obsel collection
        obsels_uri = URIRef(uri + "@obsels")
        graph = Graph(service.store, uri)
        graph.add((uri, KTBS.hasObselCollection, obsels_uri))
        obsels_graph = Graph(identifier=obsels_uri)
        if cls.RDF_MAIN_TYPE == KTBS.StoredTrace:
            obsels_cls = StoredTraceObsels
        else:
            assert cls.RDF_MAIN_TYPE == KTBS.ComputedTrace
            obsels_cls = ComputedTraceObsels
        obsels_cls.init_graph(obsels_graph, obsels_uri, uri)
        obsels_cls.create(service, obsels_uri, obsels_graph)

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
    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.StoredTrace

    RDF_EDITABLE_OUT =    [ KTBS.hasModel, KTBS.hasOrigin, KTBS.hasTraceBegin,
                            KTBS.hasTraceEnd, KTBS.hasTraceBeginDT,
                            KTBS.hasTraceEndDT, KTBS.hasDefaultSubject,
                            KTBS.hasPseudoMonRange,
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
        candidates = graph.query(_SELECT_CANDIDATE_OBSELS,
                                 initBindings=binding)
        with base.lock(self):
            for candidate, _, _ in candidates:
                ret1 = post_single_obsel(graph, parameters, _trust, candidate,
                                         KTBS.Obsel)
                if ret1:
                    assert len(ret1) == 1
                    ret.append(ret1[0])
        if not ret:
            raise InvalidDataError("No obsel found in posted graph")
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
        created = service.get(uri, cls.RDF_MAIN_TYPE)
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
        super(ComputedTrace, self).force_state_refresh(parameters)
        if self.metadata.value(self.uri, METADATA.dirty, None) is not None:
            # we *first* unset the dirty bit, so that recursive calls to
            # get_state do not result in an infinite recursion
            self.metadata.remove((self.uri, METADATA.dirty, None))
            with self.edit(_trust=True) as editable:
                editable.remove((self.uri, KTBS.hasDiagnosis, None))
                editable.remove((self.uri, KTBS.hasModel, None))
                editable.remove((self.uri, KTBS.hasOrigin, None))
                diag = self._method_impl.compute_trace_description(self)
                if not diag:
                    editable.add((self.uri, KTBS.hasDiagnosis,
                                     Literal(str(diag))))


    ######## Private method  ########

    __method_impl = None

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

    def _mark_dirty(self):
        """I force my computed data and obsels to be recomputed.

        Note that the recomputation will only occur when my state (or the state
        of my obsel collection) is required.
        """
        self.metadata.add((self.uri, METADATA.dirty, Literal("yes")))
        obsels = self.obsel_collection
        obsels.metadata.add((obsels.uri, METADATA.dirty, Literal("yes")))

    @property
    def _method_impl(self):
        """I hold the python object implementing my method.
        """
        ret = self.__method_impl
        if ret is None:
            met = self.get_method()
            while True:
                par = getattr(met, "parent", None)
                if par is None:
                    break
                met = par
            ret = self.__method_impl = get_builtin_method_impl(met.uri, True)
        return ret
