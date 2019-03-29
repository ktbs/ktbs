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
Implementation of the filter builtin methods.
"""
from itertools import chain
import logging

from rdflib import Literal, URIRef
from rdfrest.util.iso8601 import parse_date
from rdfrest.util import check_new
from .abstract import AbstractMonosourceMethod, NOT_MON, PSEUDO_MON, STRICT_MON
from .utils import copy_obsel, translate_node
from ..engine.builtin_method import register_builtin_method_impl
from ..namespace import KTBS
from ..time import get_converter_to_unit, lit2datetime #pylint: disable=E0611

# pylint is confused by a module named time (as built-in module)

LOG = logging.getLogger(__name__)

class _FilterMethod(AbstractMonosourceMethod):
    """I implement the filter builtin method.
    """
    uri = KTBS.filter

    parameter_types = {
        "origin": Literal,
        "model": URIRef,
        "before": int,
        "after": int,
        "beforeDT": parse_date,
        "afterDT": parse_date,
        "bgp": unicode,
        "otypes":
            lambda txt: txt and [ URIRef(i) for i in txt.split(" ") ] or None,
    }

    def init_state(self, computed_trace, params, cstate, diag):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.init_state
        """
        cstate.update([
            ("maxtime", None),
            ("mintime", None),
            ("otypes", None),
            ("bgp", None),
            ("passed_maxtime", False),
            ("last_seen_u", None),
            ("last_seen_b", None),
        ])
        source = computed_trace.source_traces[0]
        if "before" in params  and  "beforeDT" in params:
            diag.append("WARN: 'before' and 'beforeDT' are both specified; "
                        "the latter will be ignored")

        if "after" in params  and  "afterDT" in params:
            diag.append("WARN: 'after' and 'afterDT' are both specified; "
                        "the latter will be ignored")
        origin_dt = None
        converter = None
        if "beforeDT" in params  or  "afterDT" in params:
            origin_dt = lit2datetime(source.origin)
            if origin_dt is None:
                diag.append("'beforeDT' and/or 'afterDT' used, but trace "
                            "origin is not a valid dateTime")
            converter = get_converter_to_unit(source.unit)
            if converter is None:
                diag.append("'beforeDT' and/or 'afterDT' used, but no "
                            "converter is available for unit <%s>"
                            % source.unit)
            if origin_dt is None or converter is None:
                return

        maxtime = params.get("before")
        if maxtime is None  and  "beforeDT" in params:
            maxtime = converter(params.get("beforeDT") - origin_dt)
        cstate["maxtime"] = maxtime
        mintime = params.get("after")
        if mintime is None  and  "afterDT" in params:
            mintime = converter(params.get("afterDT") - origin_dt)
        cstate["mintime"] = mintime
        cstate["otypes"] = otypes = params.get("otypes")
        if otypes:
            m = source.get_model()
            all_subtypes = chain(*(
                robust_iter_subtypes(m, i) for i in otypes ))
            cstate["otypes"] = list(set(all_subtypes))
        cstate["bgp"] = params.get("bgp")


    def do_compute_obsels(self, computed_trace, cstate, monotonicity, diag):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.do_compute_obsels
        """
        if cstate['passed_maxtime']  and  monotonicity is STRICT_MON:
            return

        source = computed_trace.source_traces[0]
        source_obsels = source.obsel_collection
        target_obsels = computed_trace.obsel_collection
        mintime = cstate["mintime"]
        maxtime = cstate["maxtime"]
        otypes = cstate["otypes"]
        if otypes:
            otypes = set( URIRef(i) for i in otypes )
        bgp = cstate["bgp"]
        passed_maxtime = cstate["passed_maxtime"]
        try:
            last_seen_u = cstate["last_seen_u"]
            if last_seen_u:
                last_seen_u = URIRef(last_seen_u)
            last_seen_b = cstate["last_seen_b"]
        except KeyError:
            # might be the cstate of an older version of 'filter'
            last_seen_b = cstate.pop("last_seen", None)
            last_seen_u = None
            if monotonicity is STRICT_MON:
                monotonicity = PSEUDO_MON # ensures a save recovery

        begin = mintime
        after = None
        if monotonicity is NOT_MON:
            LOG.debug("non-monotonic %s", computed_trace)
            passed_maxtime = False
            last_seen_u = last_seen_b = None
            target_obsels._empty() # friend #pylint: disable=W0212
        elif monotonicity is STRICT_MON:
            LOG.debug("strictly temporally monotonic %s", computed_trace)
            if last_seen_u:
                after = last_seen_u
        elif monotonicity is PSEUDO_MON:
            LOG.debug("pseudo temporally monotonic %s", computed_trace)
            if last_seen_b is not None:
                begin = last_seen_b - source.get_pseudomon_range()
        else:
            LOG.debug("non-temporally monotonic %s", computed_trace)

        if otypes:
            filter_otypes = ', '.join( otype.n3() for otype in otypes )
            bgp = (bgp or '') + '''?obs a ?_filter_otype_.
            FILTER(?_filter_otype_ in (%s))''' % filter_otypes

        source_uri = source.uri
        target_uri = computed_trace.uri
        source_state = source_obsels.state
        target_contains = target_obsels.state.__contains__
        target_add_graph = target_obsels.add_obsel_graph
        check_new_obs = lambda uri, g=target_obsels.state: check_new(g, uri)
        source_obsels = source.iter_obsels(after=after, begin=begin,
                                           end=maxtime, bgp=bgp, refresh="no")

        with target_obsels.edit({"add_obsels_only":1}, _trust=True):
            for obs in source_obsels:
                new_obs_uri = translate_node(obs.uri, computed_trace,
                                             source_uri, False)
                if monotonicity is not STRICT_MON\
                and target_contains((new_obs_uri, KTBS.hasTrace, target_uri)):
                    LOG.debug("--- already seen %s", new_obs_uri)
                    continue # already added

                LOG.debug("--- keeping %s", obs)
                new_obs_graph = copy_obsel(obs.uri, computed_trace, source,
                                           new_obs_uri=new_obs_uri,
                                           check_new_obs=check_new_obs,
                )
                target_add_graph(new_obs_graph)

        for obs in source.iter_obsels(begin=begin, reverse=True, limit=1):
            # iter only once on the last obsel, if any
            last_seen_u = obs.uri
            last_seen_b = obs.begin
            passed_maxtime = (maxtime is not None  and  obs.end > maxtime)

        cstate["passed_maxtime"] = passed_maxtime
        if last_seen_u is not None:
            last_seen_u = unicode(last_seen_u)
        cstate["last_seen_u"] = last_seen_u
        cstate["last_seen_b"] = last_seen_b

def robust_iter_subtypes(model, otype_uri):
    """
    Iter over subtype URIs of the given obsel type in the given model.

    If otype_uri is not declared in model,
    simply yield this URI.
    """
    otype = model.get(otype_uri)
    if otype is None:
        yield otype_uri
    else:
        for i in otype.iter_subtypes(True):
            yield i.uri

register_builtin_method_impl(_FilterMethod())
