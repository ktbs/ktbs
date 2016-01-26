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
import logging

from rdflib import Literal, RDF, URIRef, Graph
from rdfrest.util.iso8601 import parse_date
from rdfrest.util import check_new
from .abstract import AbstractMonosourceMethod, NOT_MON, PSEUDO_MON, STRICT_MON
from .utils import translate_node
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
            ("last_seen", None),
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
        cstate["otypes"] = params.get("otypes")
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
        bgp = cstate["bgp"]
        passed_maxtime = cstate["passed_maxtime"]
        last_seen = cstate["last_seen"]
        if otypes:
            otypes = set( URIRef(i) for i in otypes )

        begin = mintime
        if monotonicity is NOT_MON:
            LOG.debug("non-monotonic %s", computed_trace)
            passed_maxtime = False
            last_seen = None
            target_obsels._empty() # friend #pylint: disable=W0212
        elif monotonicity is STRICT_MON:
            LOG.debug("strictly temporally monotonic %s", computed_trace)
            if last_seen:
                begin = last_seen
        elif monotonicity is PSEUDO_MON:
            LOG.debug("pseudo temporally monotonic %s", computed_trace)
            if last_seen:
                begin = last_seen - source.get_pseudomon_range()
        else:
            LOG.debug("non-temporally monotonic %s", computed_trace)

        source_uri = source.uri
        target_uri = computed_trace.uri
        source_state = source_obsels.state
        source_triples = source_state.triples
        target_contains = target_obsels.state.__contains__
        target_add_graph = target_obsels.add_obsel_graph
        check_new_obs = lambda uri, g=target_obsels.state: check_new(g, uri)

        with target_obsels.edit({"add_obsels_only":1}, _trust=True):
            for obs in source.iter_obsels(begin=begin, bgp=bgp, refresh="no"):
                last_seen = obs.begin
                if maxtime:
                    if obs.end > maxtime:
                        LOG.debug("--- passing maxtime on %s", obs)
                        passed_maxtime = True
                        break
                if otypes:
                    obs_uri = obs.uri
                    obs_state = obs.state
                    for otype in otypes:
                        if (obs_uri, RDF.type, otype) in obs_state:
                            break
                    else: # goes with the for (NOT the if)
                        LOG.debug("--- dropping %s", obs)
                        continue

                new_obs_uri = translate_node(obs.uri, computed_trace,
                                             source_uri, False)
                if target_contains((new_obs_uri, KTBS.hasTrace, target_uri)):
                    LOG.debug("--- skipping %s", new_obs_uri)
                    continue # already added


                LOG.debug("--- keeping %s", obs)
                new_obs_graph = Graph()
                new_obs_add = new_obs_graph.add

                new_obs_add((new_obs_uri, KTBS.hasTrace, target_uri))
                new_obs_add((new_obs_uri, KTBS.hasSourceObsel, obs.uri))

                for _, pred, obj in source_triples((obs.uri, None, None)):
                    if pred == KTBS.hasTrace  or  pred == KTBS.hasSourceObsel:
                        continue
                    new_obj = translate_node(obj, computed_trace, source_uri,
                                             False, check_new_obs)
                    if new_obj is None:
                        continue # skip relations to nodes that are filtered out or not created yet
                    new_obs_add((new_obs_uri, pred, new_obj))

                for subj, pred, _ in source_triples((None, None, obs.uri)):
                    if pred == KTBS.hasTrace  or  pred == KTBS.hasSourceObsel:
                        continue
                    new_subj = translate_node(subj, computed_trace, source_uri,
                                              False, check_new_obs)
                    if new_subj is None:
                        continue # skip relations from nodes that are filtered out or not created yet
                    new_obs_add((new_subj, pred, new_obs_uri))

                target_add_graph(new_obs_graph)

        cstate["passed_maxtime"] = passed_maxtime
        cstate["last_seen"] = last_seen

register_builtin_method_impl(_FilterMethod())
