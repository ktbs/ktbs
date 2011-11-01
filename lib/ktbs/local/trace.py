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
I provide the local implementation of ktbs:StoredTrace and ktbs:ComputedTrace .
"""
from datetime import datetime, timedelta
from rdflib import Graph, Literal, URIRef
from rdfrest.resource import compute_added_and_removed

from ktbs.common.trace import StoredTraceMixin
from ktbs.common.utils import extend_api
from ktbs.iso8601 import parse_date, ParseError
from ktbs.local.base import InBaseMixin
from ktbs.local.resource import PostableResource, Resource
from ktbs.namespaces import KTBS

@extend_api
class StoredTrace(StoredTraceMixin, InBaseMixin, PostableResource):
    """I implement a local KTBS stored trace.
    """

    # KTBS API #

    # TODO create_obsel

    # RDF-REST API #

    RDF_MAIN_TYPE = KTBS.StoredTrace

    RDF_PUTABLE_OUT = [ KTBS.hasModel, KTBS.hasOrigin, KTBS.hasTraceBegin,
                        KTBS.hasTraceEnd, KTBS.hasTraceBeginDT,
                        KTBS.hasTraceEndDT, KTBS.hasDefaultSubject, ]
    RDF_CARDINALITY_OUT = [
        (KTBS.hasModel, 1, 1),
        (KTBS.hasOrigin, 1, 1),
        (KTBS.hasTraceBegin, None, 1),
        (KTBS.hasTraceBeginDT, None, 1),
        (KTBS.hasTraceEnd, None, 1),
        (KTBS.hasTraceEndDT, None, 1),
        (KTBS.hasDefaultSubject, None, 1),
        ]
    
    @classmethod
    def check_new_graph(cls, uri, new_graph, resource=None, added=None,
                        removed=None):
        """I override `rdfrest.mixins.RdfPostMixin.check_new_graph`.
        """

        # TODO check trace time bounds, if any
        #  pb: the function below assumes they are both present, fix this

        added, removed = compute_added_and_removed(new_graph, resource, added,
                                                   removed)

        diag = super(StoredTrace, cls).check_new_graph(
            uri, new_graph, resource, added, removed)

        if resource:
            res = added.query("PREFIX k: <%s>"
                              "SELECT * WHERE {"
                              "  { <%s> k:hasOrigin ?t } UNION "
                              "  { <%s> k:hasTraceBegin ?t } UNION "
                              "  { <%s> k:hasTraceBeginDT ?t } UNION "
                              "  { <%s> k:hasTraceEnd ?t } UNION "
                              "  { <%s> k:hasTraceEndDT ?t } } "
                              % (KTBS, uri, uri, uri, uri, uri)
                              )
            check_timestamps = bool(res)
        else:
            check_timestamps = True

        if check_timestamps:
            origin = new_graph.value(uri, _HAS_ORIGIN)
            try:
                origin = parse_date(origin)
            except ParseError:
                pass
            begin_i = new_graph.value(_HAS_TRACE_BEGIN)
            begin_d = new_graph.value(_HAS_TRACE_BEGIN_DT)
            end_i = new_graph.value(_HAS_TRACE_END)
            end_d = new_graph.value(_HAS_TRACE_END_DT)
            if not check_timestamp(begin_i, begin_d, origin):
                diag.append("Inconsistent traceBegin timestamps")
            if not check_timestamp(end_i, end_d, origin):
                diag.append("Inconsistent traceEnd timestamps")
            if cmp_timestamps(begin_i, begin_d, end_i, end_d, origin) > 0:
                diag.append("traceBegin > traceEnd")

        return diag

    @classmethod
    def store_graph(cls, service, uri, new_graph, resource=None):
        """I override `rdfrest.mixins.RdfPostMixin.store_graph`.
        """
        origin = new_graph.value(uri, _HAS_ORIGIN)
        try:
            origin = parse_date(origin)
            complete_timestamp(new_graph, uri, _HAS_TRACE_BEGIN,
                               _HAS_TRACE_BEGIN_DT, origin)
            complete_timestamp(new_graph, uri, _HAS_TRACE_END,
                               _HAS_TRACE_END_DT, origin)
        except ParseError:
            pass

        super(StoredTrace, cls).store_graph(service, uri, new_graph, resource)

        if resource is None:
            obsels_uri = URIRef("@obsels", uri)
            Graph(service.store, uri).add((uri, _HAS_OBSEL_SET, obsels_uri))
            empty = Graph()
            StoredTraceObsels.store_graph(service, obsels_uri, empty)
        

    def find_created(self, new_graph, query=None):
        """I override `rdfrest.mixins.RdfPostMixin.find_created`.

        I only search for nodes that have ktbs:hasTrace this trace.
        """
        if query is None:
            query = "SELECT ?c WHERE { ?c <%s> <%%(uri)s> }" % _HAS_TRACE
        return super(StoredTrace, self).find_created(new_graph, query)

    def get_created_class(self, rdf_type):
        """I override `rdfrest.mixins.RdfPostMixin.get_created_class`.

        I return Obsel regardless of the type, because Obsels do not have
        explicitly the type ktbs:Obsel.
        """
        return Obsel

class StoredTraceObsels(Resource):
    """I implement the aspect resource of a stored trace containing the obsels.
    """

    RDF_MAIN_TYPE = KTBS._StoredTraceObsels #pylint: disable=W0212

# time management functions #

def timedelta_in_ms(delta):
    """Compute the number of milliseconds in a timedelta.
    """
    return (delta.microseconds / 1000 +
            (delta.seconds + delta.days * 24 * 3600) * 1000)

def check_timestamp(time_il, time_dl, origin):
    """Check that timespamp arguments are consistent.

    Consistent means:
    * if time_il is not None, it is coercible to an integer;
    * if time_dl is not None, it is coercible to a datetime;
    * if origin is a str, time_dl is None;
    * if both time_il and time_dl are not None, they represent the same point
      in time;

    :param time_il: the timestamp in ms since origin, or None
    :type  time_il: Literal with datatype xsd:integer
    :param time_dl: the timestamp in calendar time, or None
    :type  time_dl: Literal with datatype xsd:datetime
    :param origin: the origin of the trace
    :type  origin: datetime or str

    """
    if not isinstance(origin, datetime):
        return (time_dl is None)                                          

    if time_il is None or time_dl is None:
        return True

    if time_il is not None:
        time_i = time_il.toPython()
        if not isinstance(time_i, int):
            return False
    if time_dl is not None:
        time_d = parse_date(time_dl)
        if not isinstance(time_d, datetime):
            return False
    if time_il is not None and time_dl is not None:
        time_di = timedelta_in_ms(time_d - origin)
        return (time_i == time_di)

def cmp_timestamps(t1i, t1d, t2i, t2d, origin):
    """Compare two timestamps provided as integer and/or datetime.

    Assume that t1i and t1d (resp. t2i and t2d) are consistent w.r.t.
    origin. Try to compare compatible representations, or do the conversion
    if needed.

    If both values for one (or the two) timestamp(s) are None, I will return
    None.

    :param t1i: the first timestamp in ms since origin, or None
    :type  t1i: Literal with datatype xsd:integer
    :param t1d: the first timestamp in calendar time, or None
    :type  t1d: Literal with datatype xsd:datetime
    :param t2i: the second timestamp in ms since origin, or None
    :type  t2i: Literal with datatype xsd:integer
    :param t2d: the second timestamp in calendar time, or None
    :type  t2d: Literal with datatype xsd:datetime
    :param origin: the origin of the trace
    :type  origin: datetime or str

    """
    if (t1i is None and t1d is None) or (t2i is None and t2d is None):
        return None

    if t1i is not None and t2i is not None:
        return cmp(t1i, t2i)
    elif t1d is not None and t2d is not None:
        return cmp(t1d, t2d)

    # no compatible representations; convert to int
    assert isinstance(origin, datetime) # or we would not have datetimes...
    if t1i is None:
        t1i = timedelta_in_ms(t1d - origin)
    if t2i is None:
        t2i = timedelta_in_ms(t2d - origin)
    return cmp(t1i, t2i)

def complete_timestamp(graph, subject, pred_i, pred_d, origin):
    """Complete missing values in `graph` for a timestamp.

    :param graph: the graph to complete
    :type  graph: rdflib.Graph
    :param subject: the resource holding the timestamp
    :type  subject: rdflib.Node
    :param pred_i: the predicate for the integer timestamp
    :type  pred_i: rdflib.URIRef
    :param pred_d: the predicate for the datetime timestamp
    :type  pred_d: rdflib.URIRef
    :param origin: the origin of the trace
    :type  origin: datetime
    """
    time_i = graph.value(subject, pred_i)
    time_d = graph.value(subject, pred_d)
    if time_i is None and time_d is None:
        return
    if time_i is not None and time_d is not None:
        return
    if time_i is None:
        time_i = timedelta_in_ms(time_d - origin)
        graph.add(subject, pred_i, Literal(time_i))
    if time_d is None:
        time_d = origin + timedelta(milliseconds=time_i)
        graph.add(subject, pred_d, Literal(time_d))
        
    
# import Obsel in the end, as it is logically "below" trace
from ktbs.local.obsel import Obsel

_HAS_OBSEL_SET = KTBS.hasObselCollection
_HAS_ORIGIN = KTBS.hasOrigin
_HAS_TRACE = KTBS.hasTrace
_HAS_TRACE_BEGIN = KTBS.hasTraceBegin
_HAS_TRACE_BEGIN_DT = KTBS.hasTraceBeginDT
_HAS_TRACE_END = KTBS.hasTraceEnd
_HAS_TRACE_END_DT = KTBS.hasTraceEndDT
