# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
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
I provide the pythonic interface of ktbs:StoredTrace and ktbs:ComputedTrace.
"""
from numbers import Integral, Real

from rdflib import Graph, Literal, RDF, RDFS, URIRef
from rdflib.term import Node

from datetime import datetime
from rdfrest.cores.factory import factory as universal_factory
from rdfrest.exceptions import InvalidParametersError, MethodNotAllowedError
from rdfrest.util.iso8601 import parse_date, ParseError, UTC
from rdfrest.util import cache_result, coerce_to_node, coerce_to_uri
from .base import InBaseMixin
from .method import WithParametersMixin
from .obsel import ObselMixin, ObselProxy
from rdfrest.wrappers import get_wrapped, register_wrapper
from .trace_obsels import AbstractTraceObselsMixin
from ..namespace import KTBS
from ..utils import extend_api


@extend_api
class AbstractTraceMixin(InBaseMixin):
    """
    I provide the pythonic interface common to all kTBS traces.
    """

    ######## Abstract kTBS API ########

    def get_obsel(self, id):
        """
        Return the obsel with the given uri.

        :param id: the URI of the obsel; may be relative to the URI of the trace
        :type  id: str

        :rtype: `~.obsel.ObselMixin`
        """
        #  Redefining built-in id #pylint: disable-msg=W0622
        uri = coerce_to_uri(id, self.uri)
        ret = self.factory(uri, KTBS.Obsel)
        assert ret is None  or  isinstance(ret, ObselMixin)
        return ret

    def get_model(self):
        """
        I return the trace model of this trace.

        :rtype: `~.trace_model.TraceModelMixin`
        """
        tmodel_uri = self.state.value(self.uri, KTBS.hasModel)
        return universal_factory(tmodel_uri)
        # must be a .trace_model.TraceModelMixin

    def get_origin(self, as_datetime=False):
        """
        I return the origin of this trace.

        If `as_datetime` is true, get_origin will try to convert the return
        value to datetime, or return it unchanged if that fails.

        """
        origin = self.state.value(self.uri, KTBS.hasOrigin)
        if as_datetime:
            try:
                origin = parse_date(origin)
            except ParseError:
                pass
        elif origin is not None:
            origin = unicode(origin)
        return origin

    def iter_obsels(self, begin=None, end=None, reverse=False, bgp=None, refresh=None):
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
        * bgp: an additional SPARQL Basic Graph Pattern to filter obsels
        * refresh: 

          - if "no", prevent force_state_refresh to be called
          - if None or "default", force_state_refresh will be called
          - if "yes" or "force", will force recomputation of a ComputedTrace
            even if the sources have not change
          - if "recursive", will recursively force recomputatioon as above

        In the `bgp` parameter, notice that:

        * the variable `?obs` is bound each obsel
        * the `m:` prefix is bound to the trace model

        NB: the order of "recent" obsels may vary even if the trace is not
        amended, since collectors are not bound to respect the order in begin
        timestamps and identifiers.
        """
        parameters = {}
        filters = []
        postface = ""
        if begin is not None:
            if isinstance(begin, Real):
                pass # nothing else to do
            elif isinstance(begin, datetime):
                raise NotImplementedError(
                    "datetime as begin is not implemented yet")
            elif isinstance(begin, ObselMixin):
                begin = begin.begin
            else:
                raise ValueError("Invalid value for `begin` (%r)" % begin)
            filters.append("?b >= %s" % begin)
            parameters["minb"] = begin
        if end is not None:
            if isinstance(end, Real):
                pass # nothing else to do
            elif isinstance(end, datetime):
                raise NotImplementedError(
                    "datetime as end is not implemented yet")
            elif isinstance(end, ObselMixin):
                end = end.end
            else:
                raise ValueError("Invalid value for `end` (%r)" % end)
            filters.append("?e <= %s" % end)
            parameters["maxe"] = end
        if reverse:
            postface += "ORDER BY DESC(?e) DESC(?b) DESC(?obs)"
        else:
            postface += "ORDER BY ?b ?e ?obs"
        if bgp is None:
            bgp = ""
        else:
            bgp = "%s" % bgp
        if refresh:
            parameters['refresh'] = refresh
        if not parameters:
            parameters = None
        if filters:
            filters = "FILTER(%s)" % (" && ".join(filters))
        else:
            filters = ""

        collection = self.obsel_collection
        collection.force_state_refresh(parameters)
        if isinstance(collection, OpportunisticObselCollection):
            obsels_graph = collection.get_state(parameters)
        else:
            # we have the raw resource instead, so we access the whole graph
            # (pylint does not know that, hence the directive below)
            obsels_graph = collection.state #pylint: disable=E1101
        query_str = """
            SELECT ?b ?e ?obs WHERE {
                ?obs <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> <%s> ;
                     <http://liris.cnrs.fr/silex/2009/ktbs#hasBegin> ?b ;
                     <http://liris.cnrs.fr/silex/2009/ktbs#hasEnd> ?e .
                %s
                %s
            } %s
        """ % (self.uri, filters, bgp, postface)
        tuples = list(obsels_graph.query(query_str, initNs={"m": self.model_prefix}))
        for _, _, obs_uri in tuples:
            types = obsels_graph.objects(obs_uri, RDF.type)
            cls = get_wrapped(ObselProxy, types)
            yield cls(obs_uri, collection, obsels_graph, parameters)

    def iter_source_traces(self):
        """
        I iter over the sources of this computed trace.
        """
        factory = self.factory
        for uri in self.state.objects(self.uri, KTBS.hasSource):
            src = factory(uri)
            assert isinstance(src, AbstractTraceMixin)
            yield src

    def iter_transformed_traces(self):
        """
        Iter over the traces having this trace as a source.
        """
        self.force_state_refresh() # as changes can come from other resources
        factory = self.factory
        for uri in self.state.subjects(KTBS.hasSource, self.uri):
            tra = factory(uri)
            assert isinstance(tra, AbstractTraceMixin), uri
            yield tra

    def add_source_trace(self, val):
        """I add a source trace to this trace
        """
        source_uri = coerce_to_uri(val)
        # do not trust edit, as there are many verifications to make
        with self.edit() as editable:
            editable.add((self.uri, KTBS.hasSource, source_uri))
        
    def del_source_trace(self, val):
        """I break the link between this trace and one of its source traces
        """
        source_uri = coerce_to_uri(val)
        # do not trust edit, as there are many verifications to make
        with self.edit() as editable:
            editable.remove((self.uri, KTBS.hasSource, source_uri))


    ######## Extension to the abstract kTBS API ########

    def get_model_uri(self):
        """
        I return the URI of the trace model of this trace.
        """
        tmodel_uri = self.state.value(self.uri, KTBS.hasModel)
        return tmodel_uri

    def get_model_prefix(self, _NICE_SUFFIX={"#", "/"}):
        """
        I return a prefix-friendly version of the model URI for this trace.
        """
        prefix_uri = self.state.value(self.uri, KTBS.hasModel)
        if prefix_uri[-1] not in _NICE_SUFFIX:
            prefix_uri = URIRef(prefix_uri + "#")
        return prefix_uri

    @property
    @cache_result
    def obsel_collection(self):
        """This trace's obsel collection as a raw resource.

        :rtype: `.trace_obsels.AbstractTraceObselsMixin`:class:
        """
        return OpportunisticObselCollection(self)

    def get_pseudomon_range(self):
        """Return the pseudo-monotonicity range of this trace.

        If the pseudo-monotonicity range is X, all changes applied less than X
        time-units before the last obsel will be considered pseudo-monotonic.
        
        TODO DOC reference to a detailed explaination about monotonicity.
        """
        return int(self.state.value(self.uri, KTBS.hasPseudoMonRange) or 0)

    def set_pseudomon_range(self, val):
        """Return the pseudo-monotonicity range of this trace.

        :see-also: `get_pseudomon_range`:meth:

        TODO DOC reference to a detailed explaination about monotonicity.
        """
        assert isinstance(val, Real)
        assert val >= 0
        if val == 0:
            val = None
        with self.edit(_trust=True) as editable:
            editable.set((self.uri, KTBS.hasPseudoMonRange, Literal(val)))


@register_wrapper(KTBS.StoredTrace)
@extend_api
class StoredTraceMixin(AbstractTraceMixin):
    """
    I provide the pythonic interface common to kTBS stored traces.
    """
    ######## Abstract kTBS API ########

    def set_model(self, model):
        """I set the model of this trace.
        model can be a Model or a URI; relative URIs are resolved against this
        trace's URI.
        """
        model_uri = coerce_to_uri(model, self.uri)
        with self.edit(_trust=True) as graph:
            graph.set((self.uri, KTBS.hasModel, model_uri))

    def set_origin(self, origin):
        """I set the origin of this trace.
        origin can be a string or a datetime.
        """
        isoformat = getattr(origin, "isoformat", None)
        if isoformat is not None:
            origin = isoformat()
        origin = Literal(origin)
        with self.edit(_trust=True) as graph:
            graph.set((self.uri, KTBS.hasOrigin, origin))

    def get_default_subject(self):
        """
        I return the default subject of this trace.
        """
        ret = self.state.value(self.uri, KTBS.hasDefaultSubject)
        if ret is not None:
            ret = unicode(ret)
        return ret

    def set_default_subject(self, subject):
        """I set the default subject of this trace.
        """
        subject = Literal(subject)
        with self.edit(_trust=True) as graph:
            graph.set((self.uri, KTBS.hasDefaultSubject, subject))

    def create_obsel(self, id=None, type=None, begin=None, end=None, 
                     subject=None, attributes=None, relations=None, 
                     inverse_relations=None, source_obsels=None, label=None,
                     no_return=False):
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
        :param no_return: if True, None will be returned instead of the created obsek;
            this saves time and (in the case of a remote kTBS) network traffic

        :rtype: `ktbs.client.obsel.Obsel`
        """
        # redefining built-in 'id' #pylint: disable=W0622

        # We somehow duplicate Obsel.complete_new_graph and
        # Obsel.check_new_graph here, but this is required if we want to be
        # able to set _trust=True below.
        # Furthermore, the signature of this method makes it significantly
        # easier to produce a valid graph, so there is a benefit to this
        # duplication.
            
        if type is None:
            raise ValueError("type is mandatory for obsel creation")
        if begin is None:
            begin = _NOW(UTC)
        if end is None:
            end = begin
        if subject is None:
            subject = self.get_default_subject()
            if subject is None:
                raise ValueError("subject is mandatory since trace has no "
                                 "default subject")

        trust = False # TODO SOON decide if we can trust anything
        # this would imply verifying that begin and end are mutually consistent
        # knowing that they could be heterogeneous (int/datetime)
        graph = Graph()
        obs = coerce_to_node(id, self.uri) # return BNode if id is None
        type_uri = coerce_to_uri(type, self.uri)
        graph.add((obs, RDF.type, type_uri))
        graph.add((obs, KTBS.hasTrace, self.uri))

        if isinstance(begin, Integral):
            graph.add((obs, KTBS.hasBegin, Literal(int(begin))))
        else: # will use KTBS.hasBeginDT
            begin_dt = begin
            if isinstance(begin, basestring):
                begin_dt = parse_date(begin_dt)
            elif isinstance(begin, datetime):
                if begin.tzinfo is None:
                    begin = begin.replace(tzinfo=UTC)
            else:
                raise ValueError("Could not interpret begin %s", begin)
            graph.add((obs, KTBS.hasBeginDT, Literal(begin_dt)))

        if isinstance(end, Integral):
            graph.add((obs, KTBS.hasEnd, Literal(int(end))))
        else: # will use KTBS.hasEndDT
            end_dt = end
            if isinstance(end_dt, basestring):
                end_dt = parse_date(end_dt)
            elif isinstance(end, datetime):
                if end.tzinfo is None:
                    end = end.replace(tzinfo=UTC)
            else:
                raise ValueError("Could not interpret end %s", end)
            graph.add((obs, KTBS.hasEndDT, Literal(end_dt)))

        if subject is not None:
            graph.add((obs, KTBS.hasSubject, Literal(subject)))

        if attributes is not None:
            for key, val in attributes.items():
                k_uri = coerce_to_uri(key)
                if isinstance(val, Node):
                    v_node = val
                else:
                    v_node = Literal(val)
                    # TODO LATER do something if val is a list
                graph.add((obs, k_uri, v_node))

        if relations is not None:
            for rtype, other in relations:
                rtype_uri = coerce_to_uri(rtype)
                other_uri = coerce_to_uri(other)
                graph.add((obs, rtype_uri, other_uri))

        if inverse_relations is not None:
            for other, rtype in inverse_relations:
                other_uri = coerce_to_uri(other)
                rtype_uri = coerce_to_uri(rtype)
                graph.add((other_uri, rtype_uri, obs))

        if source_obsels is not None:
            for src in source_obsels:
                s_uri = coerce_to_uri(src)
                graph.add((obs, KTBS.hasSourceObsel, s_uri))

        if label is not None:
            graph.add((obs, RDFS.label, Literal(label)))

        uris = self.post_graph(graph, None, trust, obs, KTBS.Obsel)
        assert len(uris) == 1
        self.obsel_collection.force_state_refresh()
        if not no_return:
            ret = self.factory(uris[0], KTBS.Obsel)
            assert isinstance(ret, ObselMixin)
            return ret

@register_wrapper(KTBS.ComputedTrace)
@extend_api
class ComputedTraceMixin(WithParametersMixin, AbstractTraceMixin):
    """
    I provide the pythonic interface common to kTBS computed traces.
    """

    ######## Abstract kTBS API ########

    def get_method(self):
        """I return the method used by this computed trace
        """
        return universal_factory(self.state.value(self.uri, KTBS.hasMethod))
        # must return a .method.MethodMixin

    def set_method(self, val):
        """I set the method that this computed trace will use
        """
        method_uri = coerce_to_uri(val)
        # do not trust edit, as there is many verifications to make
        with self.edit() as editable:
            editable.set((self.uri, KTBS.hasMethod, method_uri))
        self.force_state_refresh()
        self.obsel_collection.force_state_refresh()


    def add_source_trace(self, val):
        """I override :meth:`AbstractTraceMixin.add_source_trace`

        I force the refresh of this trace after the change, as it may have
        changed computed properties.
        """
        super(ComputedTraceMixin, self).add_source_trace(val)
        self.force_state_refresh()
        self.obsel_collection.force_state_refresh()
        
    def del_source_trace(self, val):
        """I override :meth:`AbstractTraceMixin.del_source_trace`

        I force the refresh of this trace after the change, as it may have
        changed computed properties.
        """
        super(ComputedTraceMixin, self).del_source_trace(val)
        self.force_state_refresh()
        self.obsel_collection.force_state_refresh()

    def set_parameter(self, key, value):
        """I override :meth:`.method.WithParametersMixin.set_parameter`

        I force the refresh of this trace after the change, as it may have
        changed computed properties.
        """
        super(ComputedTraceMixin, self).set_parameter(key, value)
        self.force_state_refresh()
        self.obsel_collection.force_state_refresh()

    def del_parameter(self, key):
        """I override :meth:`.method.WithParametersMixin.del_parameter`

        I force the refresh of this trace after the change, as it may have
        changed computed properties.
        """
        super(ComputedTraceMixin, self).del_parameter(key)
        self.force_state_refresh()
        self.obsel_collection.force_state_refresh()

    ######## Extension to the abstract kTBS API ########

    def get_diagnosis(self, force_refresh=False):
        """I return the diagnosis of the last execution of this computed trace.

        Note that the diagnosis is None iff the execution succeeded.
        """
        ret = self.state.value(self.uri, KTBS.hasDiagnosis)
        if ret is not None:
            ret = unicode(ret)
        return ret

    ######## Private methods ########

    def _get_inherited_parameters(self):
        """
        Required by WithParametersMixin.
        """
        return getattr(self.method, "parameters_as_dict", None) or {}
        

@extend_api
class OpportunisticObselCollection(AbstractTraceObselsMixin):
    """I implement :class:`rdfrest.cores.ICore` for obsel collections.

    Obsel collections in kTBS can become very big, possibly to the point where
    a server will refuse to serve the full graph at once. Fortunately, they
    accept a number of query-string parameters to request only "slices" of
    the collection.

    This implementation retrieves slices of the obsel collection in an
    opportunistic way (*i.e.* finding a trade-off between how much the
    kTBS is willing to provide at a time and what is actually requested by the
    code using it).

    The graph returned by :meth:`get_state` will always contain all the obsels
    specified by the `parameters` passed to it, *but possibly more*.
    """
    # *** WARNING ***: the description below is a plan for the future
    # for the moment, this is a naive implementation, just forwarding all
    # calls to the actual, plain, resource

    # TODO SOON implement the mechanism below,
    # and remove warning above

    # The resource maintains a list of slices, obtained with
    # self.trace.factory (hence with the appropriate implementation).
    #
    # Whenever get_state or force_state_refresh is called with parameters,
    # we first check if (a subset of) the slices we have cover it all;
    # if not, we try to get the missing slices;
    # note that, in the case of a remote server, the server may refuse to serve
    # a slice which is deemed too big; in that case, we recursively split the
    # requested slice until we manage to get everything we need;
    # for get_state, we then return a ReadOnlyAggregateGraph of the graphs of
    # the relevant slices.
    #
    # We have to take care of the "open slice" (a slice with no upper bound)
    # as it can become too big at some point; when this happens, we replace
    # with a corresponding "closed" slice of acceptable size, and a new
    # open slice completeing it.

    def __init__(self, trace):
        # not calling ICore.__init__ #pylint: disable=W0231
        self.uri = trace.state.value(trace.uri, KTBS.hasObselCollection)
        self.actual = trace.factory(self.uri)
        self.slices = None
        self._trace = trace

    def __str__(self):
        return "<%s>" % self.uri

    ######## ICore implementation ########

    def factory(self, uri, _rdf_type=None, _no_spawn=False):
        """I implement :meth:`.cores.ICore.factory`.

        I simply rely on the factory of my trace.
        """
        return self.actual.factory(uri, _rdf_type, _no_spawn)

    def get_state(self, parameters=None):
        """I implement :meth:`.cores.ICore.get_state`.
        """
        return self.actual.get_state(parameters)

    def force_state_refresh(self, parameters=None):
        """I implement `interface.ICore.force_state_refresh`.

        I simply force a state refresh on my trace.
        """
        return self.actual.force_state_refresh(parameters)

    def edit(self, parameters=None, clear=False, _trust=False):
        """I implement :meth:`.cores.ICore.edit`.

        I try to edit the whole graph.
        """
        if parameters is not None:
            raise InvalidParametersError(" ".join(parameters))
        if clear:
            raise NotImplementedError
            # we must check if get_state has been called once without any
            # parameter (i.e. the caller code knows the whole graph) else
            # we fail with ValueError
        return self.actual.edit(None, clear, _trust)


    def post_graph(self, graph, parameters=None,
                   _trust=False, _created=None, _rdf_type=None):
        """I implement :meth:`.cores.ICore.post_graph`.

        Obsel collection do not support post_graph.
        """
        # unused arguments #pylint: disable=W0613
        raise MethodNotAllowedError("Can not post to obsel collection %s"
                                    % self)

    def delete(self, parameters=None, _trust=False):
        """I implement :meth:`.cores.ICore.delete`.

        Delegate to proper obsel resource.
        """
        return self.actual.delete(parameters, _trust)

_NOW = datetime.now
