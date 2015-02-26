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
from json import dumps as json_dumps, loads as json_loads
import logging

from rdflib import Literal, RDF, URIRef

from rdfrest.util.iso8601 import parse_date, ParseError
from rdfrest.util import check_new, Diagnosis
from .interface import IMethod
from .utils import translate_node
from ..engine.builtin_method import register_builtin_method_impl
from ..engine.resource import METADATA
from ..namespace import KTBS
from ..time import get_converter_to_unit, lit2datetime #pylint: disable=E0611

# pylint is confused by a module named time (as built-in module)

LOG = logging.getLogger(__name__)

class _FilterMethod(IMethod):
    """I implement the filter builtin method.
    """
    uri = KTBS.filter

    def compute_trace_description(self, computed_trace):
        """I implement :meth:`.interface.IMethod.compute_trace_description`.
        """
        diag = Diagnosis("filter.compute_trace_description")
        cstate = { "method": "filter",
                   "before": None,
                   "after": None,
                   "otypes": None,
                   "bgp": None,
                   "finished": False,
                   "last_seen": None,
                   "log_mon_tag": None,
                   "str_mon_tag": None,
                   }

        src, params =  self._prepare_source_and_params(computed_trace, diag)
        if src is not None:
            assert params is not None
            model = params.get("model")
            if model is None:
                model = src.model_uri
            else:
                model = URIRef(model)
            origin = Literal(params.get("origin")  or  src.origin)
            with computed_trace.edit(_trust=True) as editable:
                editable.add((computed_trace.uri, KTBS.hasModel, model))
                editable.add((computed_trace.uri, KTBS.hasOrigin, origin))

            converter = None
            if "beforeDT" in params  or  "afterDT" in params:
                origin_dt = lit2datetime(origin)
                if origin_dt is None:
                    diag.append("'beforeDT' and/or 'afterDT' used, but trace "
                                "origin is not a valid dateTime")
                converter = get_converter_to_unit(computed_trace.unit)
                if converter is None:
                    diag.append("'beforeDT' and/or 'afterDT' used, but no "
                                "converter is available for unit <%s>"
                                % computed_trace.unit)

            before = params.get("before")
            if before is None  and  "beforeDT" in params:
                before = converter(params.get("beforeDT") - origin_dt)
            cstate["before"] = before
            after = params.get("after")
            if after is None  and  "afterDT" in params:
                after = converter(params.get("afterDT") - origin_dt)
            cstate["after"] = after
            cstate["otypes"] = params.get("otypes")
            cstate["bgp"] = params.get("bgp")

        if not diag:
            cstate["errors"] = list(diag)


        computed_trace.metadata.set((computed_trace.uri,
                                     METADATA.computation_state,
                                     Literal(json_dumps(cstate))
                                     ))

        return diag

    def compute_obsels(self, computed_trace, from_scratch=False):
        """I implement :meth:`.interface.IMethod.compute_obsels`.
        """
        diag = Diagnosis("filter.compute_obsels")
        cstate = json_loads(
            computed_trace.metadata.value(computed_trace.uri,
                                          METADATA.computation_state))
        if from_scratch:
            for key in ("finished", "last_seen", "log_mon_tag", "str_mon_tag"):
                cstate[key] = None
        errors = cstate.get("errors")
        if errors:
            for i in errors:
                diag.append(i)
                return diag

        source = computed_trace.source_traces[0]
        source_obsels = source.obsel_collection
        target_obsels = computed_trace.obsel_collection
        after = cstate["after"]
        before = cstate["before"]
        otypes = cstate["otypes"]
        bgp = cstate["bgp"]
        if otypes:
            otypes = set( URIRef(i) for i in otypes )
        old_log_mon_tag = cstate["log_mon_tag"]
        old_str_mon_tag = cstate["str_mon_tag"]
        last_seen = cstate["last_seen"]
        finished = cstate["finished"]

        if finished  and  old_str_mon_tag == source_obsels.str_mon_tag:
            return diag

        begin = after
        if old_log_mon_tag != source_obsels.log_mon_tag:
            # non-monotonic change; empty the graph and start anew
            target_obsels._empty() # friend #pylint: disable=W0212
            LOG.debug("non-monotonic %s", computed_trace)
        elif old_str_mon_tag == source_obsels.str_mon_tag:
            # stritcly temporally monotonic change; start at last_seen
            LOG.debug("strictly temporally monotonic %s", computed_trace)
            if last_seen:
                begin = last_seen
        else: 
            LOG.debug("non-temporally monotonic %s", computed_trace)

        source_uri = source.uri
        target_uri = computed_trace.uri
        source_state = source_obsels.state
        source_triples = source_state.triples
        with target_obsels.edit(_trust=True) as editable:
            target_contains = editable.__contains__
            target_add = editable.add

            for obs in source.iter_obsels(begin=begin, bgp=bgp, refresh="no"):
                cstate["last_seen"] = obs.begin
                if after  and  obs.begin < after:
                    LOG.debug("--- dropping %s", obs)
                    continue
                if before:
                    if obs.begin > before:
                        LOG.debug("--- finishing on %s", obs)
                        cstate["finished"] = True
                        break
                    elif obs.end > before:
                        LOG.debug("--- dropping %s", obs)
                        continue
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
                target_add((new_obs_uri, KTBS.hasTrace, target_uri))
                target_add((new_obs_uri, KTBS.hasSourceObsel, obs.uri))

                for _, pred, obj in source_triples((obs.uri, None, None)):
                    if pred == KTBS.hasTrace  or  pred == KTBS.hasSourceObsel:
                        continue
                    new_obj = translate_node(obj, computed_trace, source_uri,
                                             False)
                    if new_obj != obj and check_new(editable, new_obj):
                        continue # skip relations to node that are filtered out
                    target_add((new_obs_uri, pred, new_obj))
                for subj, pred, _ in source_triples((None, None, obs.uri)):
                    if pred == KTBS.hasTrace  or  pred == KTBS.hasSourceObsel:
                        continue
                    new_subj = translate_node(subj, computed_trace, source_uri,
                                              False)
                    if new_subj != subj and check_new(editable, new_subj):
                        continue # skip relations to node that are filtered out
                    target_add((new_subj, pred, new_obs_uri))

        cstate["str_mon_tag"] = source_obsels.str_mon_tag
        cstate["log_mon_tag"] = source_obsels.log_mon_tag

        computed_trace.metadata.set((computed_trace.uri,
                                     METADATA.computation_state,
                                     Literal(json_dumps(cstate))
                                     ))
        return diag

    @staticmethod
    def _prepare_source_and_params(computed_trace, diag):
        """I check and prepare the data required by the method.

        I return the unique source of the computed trace, and a dict of
        useful parameters converted to the expected datatype. If this can not
        be done, I return ``(None, None)``.

        I also populate `diag` with error/warning messages.
        """
        sources = computed_trace.source_traces
        params = computed_trace.parameters_as_dict
        critical = False

        if len(sources) != 1:
            diag.append("Method ktbs:filter expects exactly one source")
            critical = True

        for key, val in params.items():
            datatype = _PARAMETERS_TYPE.get(key)
            if datatype is None:
                diag.append("WARN: Parameter %s is not used by ktbs:filter"
                            % key)
            else:
                try:
                    params[key] = datatype(val)
                except ValueError:
                    diag.append("Parameter %s has illegal value: %s"
                                % (key, val))
                    critical = True
                except ParseError:
                    diag.append("Parameter %s has illegal value: %s"
                                % (key, val))
                    critical = True

        if "before" in params  and  "beforeDT" in params:
            diag.append("WARN: 'before' and 'beforeDT' are both specified; "
                        "the latter will be ignored")
        if "after" in params  and  "afterDT" in params:
            diag.append("WARN: 'after' and 'afterDT' are both specified; "
                        "the latter will be ignored")
            
        if critical:
            return None, None
        else:
            return sources[0], params


_PARAMETERS_TYPE = {
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


register_builtin_method_impl(_FilterMethod())
