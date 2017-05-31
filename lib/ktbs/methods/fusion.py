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
Implementation of the fusion builtin methods.
"""
import traceback
from json import dumps as json_dumps, loads as json_loads
import logging

from rdflib import Literal, URIRef

from rdfrest.util import Diagnosis
from .interface import IMethod
from .utils import translate_node
from ..namespace import KTBS
from ..engine.builtin_method import register_builtin_method_impl
from ..engine.resource import METADATA


LOG = logging.getLogger(__name__)

class _FusionMethod(IMethod):
    """I implement the fusion builtin method.
    """
    uri = KTBS.fusion

    def compute_trace_description(self, computed_trace, _sources=None):
        """I implement :meth:`.interface.IMethod.compute_trace_description`.
        """
        diag = Diagnosis("fusion.compute_trace_description")
        sources = _sources or computed_trace.source_traces
        params = computed_trace.parameters_as_dict
        critical = False

        if len(sources) < 1:
            diag.append("Method ktbs:fusion expects at least one source")
            critical = True
        critical, fusion_params = \
            self._get_fusion_parameters(params, diag, critical)
        for key in params:
            diag.append("WARN: Parameter %s is not used by ktbs:fusion"
                        % key)
        if not critical:
            self._do_compute_trace_description(computed_trace, sources,
                                               fusion_params, diag)
        self._init_cstate(computed_trace, diag)

        return diag

    def compute_obsels(self, computed_trace, from_scratch=False,
                       _sources=None, _diag=None):
        """I implement :meth:`.interface.IMethod.compute_obsels`.
        """
        diag = _diag if _diag is not None else Diagnosis("fusion.compute_obsels")
        cstate = json_loads(
            computed_trace.metadata.value(computed_trace.uri,
                                          METADATA.computation_state))
        if from_scratch:
            for key in ("last_seens", "old_log_mon_tags"):
                cstate[key] = {}
        errors = cstate.get("errors")
        if errors:
            for i in errors:
                diag.append(i)
                return diag
        effective_sources = _sources or computed_trace.source_traces

        # start anew if sources have changed or have been modified in a
        # non-monotonic way
        old_log_mon_tags = cstate["old_log_mon_tags"]
        target_obsels = computed_trace.obsel_collection
        for src in effective_sources:
            old_tag = old_log_mon_tags.get(src.uri)
            if old_tag != src.obsel_collection.log_mon_tag:
                target_obsels._empty() # friend #pylint: disable=W0212
                LOG.debug("non-monotonic %s", computed_trace)
                cstate["last_seens"] = {}
                cstate["old_log_mon_tags"] = old_log_mon_tags = {}
                break
        if not old_log_mon_tags:
            cstate["old_log_mon_tags"] = old_log_mon_tags = dict(
                (src.uri, src.obsel_collection.log_mon_tag)
                for src in effective_sources
                )
        
        last_seens = cstate["last_seens"]
        target_uri = computed_trace.uri
        with target_obsels.edit(_trust=True) as editable:
            target_contains = editable.__contains__
            target_add = editable.add
            for src in effective_sources:
                src_uri = src.uri
                src_triples = src.obsel_collection.get_state({"refresh":"no"}).triples
                for obs in src.iter_obsels(begin=last_seens.get(src_uri), refresh="no"):
                    last_seens[src_uri] = obs.begin

                    new_obs_uri = translate_node(obs.uri, computed_trace,
                                                 src_uri, True)
                    if target_contains((new_obs_uri,
                                        KTBS.hasTrace,
                                        target_uri)):
                        LOG.debug("--- skipping %s", new_obs_uri)
                        continue # already added

                    LOG.debug("--- keeping %s", obs)
                    target_add((new_obs_uri, KTBS.hasTrace, target_uri))
                    target_add((new_obs_uri, KTBS.hasSourceObsel, obs.uri))

                    for _, pred, obj in src_triples((obs.uri, None, None)):
                        if pred == KTBS.hasTrace \
                        or pred == KTBS.hasSourceObsel:
                            continue
                        new_obj = translate_node(obj, computed_trace, src_uri,
                                                 True)
                        target_add((new_obs_uri, pred, new_obj))
                    for subj, pred, _ in src_triples((None, None, obs.uri)):
                        if pred == KTBS.hasTrace \
                        or pred == KTBS.hasSourceObsel:
                            continue
                        new_subj = translate_node(subj, computed_trace, src_uri,
                                                  True)
                        target_add((new_subj, pred, new_obs_uri))
        

        computed_trace.metadata.set((computed_trace.uri,
                                     METADATA.computation_state,
                                     Literal(json_dumps(cstate))
                                     ))
        return diag

    @staticmethod
    def _get_fusion_parameters(params, diag, critical):
        """I check and consume fusion-related parameters from params.

        I also populate `diag` with error/warning messages.
        
        I return a pair (critical, fusion_params)
        """

        fusion_params = {}
        for key, datatype in _PARAMETERS_TYPE.items():
            val = params.pop(key, None)
            if val is None:
                continue
            try:
                fusion_params[key] = datatype(val)
            except:
                LOG.info(traceback.format_exc())
                diag.append("Parameter %s has illegal value: %s"
                            % (key, val))
                critical = True

        return critical, fusion_params

    @staticmethod
    def _do_compute_trace_description(computed_trace, sources, fusion_params, diag):
        model = fusion_params.get("model")
        if model is not None:
            model = URIRef(model)
        else:
            models = set(src.model_uri for src in sources)
            if len(models) > 1:
                diag.append("Sources have different models and no target "
                            "model is explicitly specified")
            else:
                model = models.pop()

        origin = fusion_params.get("origin")
        if origin is None:
            origins = set(src.origin for src in sources)
            if len(origins) > 1:
                diag.append("Sources have different origins and no target "
                            "origin is explicitly specified")
            else:
                origin = origins.pop()
        origin = Literal(origin)

        with computed_trace.edit(_trust=True) as editable:
            if model:
                editable.add((computed_trace.uri, KTBS.hasModel, model))
            if origin:
                editable.add((computed_trace.uri, KTBS.hasOrigin, origin))

    @staticmethod
    def _init_cstate(computed_trace, diag):
        """I initialize the computation state of a given computed_trace
        """
        cstate = { "method": "fusion",
                   "last_seens": {},
                   "old_log_mon_tags": {},
        }

        if not diag:
            cstate["errors"] = list(diag)

        computed_trace.metadata.set((computed_trace.uri,
                                     METADATA.computation_state,
                                     Literal(json_dumps(cstate))
                                     ))



_PARAMETERS_TYPE = {
    "origin": Literal,
    "model": URIRef,
    # TODO: implement a parameter to enforce monotonicity or pseudomonotonicity?
}

register_builtin_method_impl(_FusionMethod())
