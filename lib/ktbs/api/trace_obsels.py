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
I provide the pythonic interface to kTBS obsel collections.
"""
from datetime import datetime
from numbers import Real
from rdflib import RDF, URIRef

from rdfrest.cores import ICore
from rdfrest.util import cache_result
from rdfrest.wrappers import register_wrapper

from ..namespace import KTBS
from .obsel import ObselMixin


@register_wrapper(KTBS.StoredTraceObsels)
@register_wrapper(KTBS.ComputedTraceObsels)
class AbstractTraceObselsMixin(ICore):
    """I provide the pythonic interface common to all kTBS obsel collections.
    """

    ######## Extension to the abstract kTBS API ########
    # (as this class is not defined by the API anyway)

    @property
    @cache_result
    def trace(self):
        """I return the trace owning this obsel collection.
        """
        global _TYPECONV
        trace_uri = self.state.value(None, KTBS.hasObselCollection, self.uri)
        self_type = self.state.value(self.uri, RDF.type)
        trace_type = _TYPECONV[self_type]
        return self.factory(trace_uri, [trace_type])
        # must be a .trace.AbstractTraceMixin

    @property
    @cache_result
    def trace_uri(self):
        """I return the trace owning this obsel collection.
        """
        trace_uri = self.state.value(None, KTBS.hasObselCollection, self.uri)
        return trace_uri

    def build_select(self, begin=None, end=None, after=None, before=None,
                     reverse=False, bgp=None, limit=None, offset=None,
                     selected="?obs"):
        """
        Build a SPARQL query listing the obsels of this trace.

        :rtype: `rdflib.query.Result`:class:

        NB: the SPARQL query includes no PREFIX definition,
        in order to be embedable as a subquery,
        but it *requires* the prefix ``ktbs`` to be declared
        (bound to the kTBS namespace, of course).

        The obsels are sorted by their end timestamp, then their begin
        timestamp, then their identifier. If reverse is true, the order is
        inversed.

        If given, begin and/or end are interpreted as the (included)
        boundaries of an interval; only obsels entirely contained in this
        interval will be yielded.

        * begin: an int, datetime
        * end: an int, datetime
        * after: an obsel, URIRef
        * before: an obsel, URIRef
        * reverse: an object with a truth value
        * bgp: an additional SPARQL Basic Graph Pattern to filter obsels
        * limit: an int
        * selected: the selected variables

        In the `bgp` parameter, notice that:

        * the variable `?obs` is bound each obsel
        * the `m:` prefix is bound to the trace model

        NB: the order of "recent" obsels may vary even if the trace is not
        amended, since collectors are not bound to respect the order in begin
        timestamps and identifiers.
        """
        filters = []
        postface = ""
        if bgp is None:
            bgp = ""
        else:
            bgp = "%s" % bgp
        if begin is not None:
            if isinstance(begin, Real):
                pass # nothing else to do
            elif isinstance(begin, datetime):
                raise NotImplementedError(
                    "datetime as begin is not implemented yet")
            else:
                raise ValueError("Invalid value for `begin` (%r)" % begin)
            filters.append("?b >= %s" % begin)
        if end is not None:
            if isinstance(end, Real):
                pass # nothing else to do
            elif isinstance(end, datetime):
                raise NotImplementedError(
                    "datetime as end is not implemented yet")
            else:
                raise ValueError("Invalid value for `end` (%r)" % end)
            filters.append("?e <= %s" % end)
        if after is not None:
            if isinstance(after, URIRef):
                bgp = "<{}> ktbs:hasBegin ?_ab;ktbs:hasEnd ?_ae. {}" \
                       .format(after, bgp)
                after_values = (after, "?_ab", "?_ae")
            elif isinstance(after, ObselMixin):
                after_values = (after.uri, after.begin, after.end)
            else:
                raise ValueError("Invalid value for `after` (%r)" % after)
            filters.append("?e > {2} || "
                           "?e = {2} && ?b > {1} || "
                           "?e = {2} && ?b = {1} && str(?obs) > \"{0}\""
                           .format(*after_values))
        if before is not None:
            if isinstance(before, URIRef):
                bgp = "<{}> ktbs:hasBegin ?_bb;ktbs:hasEnd ?_be. {}" \
                      .format(before, bgp)
                before_values = (before, "?_bb", "?_be")
            elif isinstance(before, ObselMixin):
                before_values = (before.uri, before.begin, before.end)
            else:
                raise ValueError("Invalid value for `before` (%r)" % before)
            filters.append("?e < {2} || "
                           "?e = {2} && ?b < {1} || "
                           "?e = {2} && ?b = {1} && str(?obs) < \"{0}\""
                           .format(*before_values))
        if reverse:
            postface += "ORDER BY DESC(?e) DESC(?b) DESC(?obs)"
        else:
            postface += "ORDER BY ?e ?b ?obs"
        if limit is not None:
            postface += " LIMIT %s" % limit
        if offset is not None:
            postface += " OFFSET %s" % offset
        if filters:
            filters = "FILTER(%s)" % (" && ".join(filters))
        else:
            filters = ""

        query_str = (
            "SELECT %s WHERE {"
                "?obs ktbs:hasTrace <%s>;ktbs:hasBegin ?b;ktbs:hasEnd ?e."
                "%s "
                "%s "
            "}%s"
        ) % (selected, self.trace_uri, filters, bgp, postface)
        return query_str

_TYPECONV = {
    KTBS.StoredTraceObsels: KTBS.StoredTrace,
    KTBS.ComputedTraceObsels: KTBS.ComputedTrace,
}
