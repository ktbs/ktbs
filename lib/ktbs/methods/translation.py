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
Implementation of the translation builtin methods.
"""
import logging

from json import loads as parseJson
from rdflib import Literal, URIRef, Graph
from rdfrest.util import replace_node_dense
from .abstract import AbstractMonosourceMethod, NOT_MON, PSEUDO_MON, STRICT_MON
from .utils import translate_node, update_obsel_relations
from ..engine.builtin_method import register_builtin_method_impl
from ..namespace import KTBS

# pylint is confused by a module named time (as built-in module)

LOG = logging.getLogger(__name__)

class _TranslationMethod(AbstractMonosourceMethod):
    """I implement the translation builtin method.
    """
    uri = KTBS.translation

    parameter_types = {
        "origin": Literal,
        "model": URIRef,
        "map": parseJson,
    }

    def init_state(self, computed_trace, params, cstate, diag):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.init_state
        """
        if "map" not in params:
            diag.append("'map' parameter is mandatory")
            return

        src_model = computed_trace.source_traces[0].model_uri
        tgt_model = computed_trace.model_uri

        map = dict(
            (unicode(URIRef(key, src_model)), unicode(URIRef(val, tgt_model)))
            for key, val in params['map'].iteritems()
        )

        cstate.update([
            ("map", map),
            ("last_seen", None),
        ])


    def do_compute_obsels(self, computed_trace, cstate, monotonicity, diag):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.do_compute_obsels
        """
        source = computed_trace.source_traces[0]
        target_obsels = computed_trace.obsel_collection

        map = dict( (URIRef(key), URIRef(val))
                    for key,val in cstate["map"].iteritems() )
        last_seen = cstate["last_seen"]
        begin = None

        if monotonicity is NOT_MON:
            LOG.debug("non-monotonic %s", computed_trace)
            last_seen = None
            target_obsels._empty() # friend #pylint: disable=W0212
        elif monotonicity is STRICT_MON:
            LOG.debug("strictly temporally monotonic %s", computed_trace)
        elif monotonicity is PSEUDO_MON:
            LOG.debug("pseudo temporally monotonic %s", computed_trace)
            begin = source.get_obsel(last_seen).begin - source.get_pseudomon_range()
            last_seen = None
        else:
            LOG.debug("non-temporally monotonic %s", computed_trace)
            last_seen = None

        source_uri = source.uri
        target_uri = computed_trace.uri
        target_contains = target_obsels._graph.__contains__
        target_add_obsel = target_obsels._add_obsel

        with target_obsels.edit({"add_obsels_only":1}, _trust=True):
            new_obsels = []
            for obs in source.iter_obsels(after=begin, refresh="no"):
                last_seen = obs.uri

                new_obs_uri = translate_node(obs.uri, computed_trace,
                                             source_uri, False)
                if target_contains((new_obs_uri, KTBS.hasTrace, target_uri)):
                    LOG.debug("--- skipping %s for %s", new_obs_uri, target_uri)
                    continue # already added


                LOG.debug("--- keeping %s for %s", obs, target_uri)
                new_obs_graph = Graph()
                new_obs_graph.addN(translated_quads(obs.state, new_obs_graph,
                                                    map, obs.uri, new_obs_uri))
                new_obs_graph.add((new_obs_uri, KTBS.hasTrace, target_uri))
                new_obs_graph.add((new_obs_uri, KTBS.hasSourceObsel, obs.uri))

                target_add_obsel(new_obs_uri, new_obs_graph)
                new_obsels.append(new_obs_uri)

            update_obsel_relations(computed_trace.service, new_obsels)

        cstate["last_seen"] = last_seen

register_builtin_method_impl(_TranslationMethod())

_EXCLUDE = {KTBS.hasTrace, KTBS.hasSourceObsel}

def translated_quads(old_graph, new_graph, map, old_obs_uri, new_obs_uri):
    for subj, pred, obj in old_graph:
        if subj == old_obs_uri:
            if pred in _EXCLUDE:
                continue
            subj = new_obs_uri
        else:
            subj = map.get(subj, subj)
        pred = map.get(pred, pred)
        if obj == old_obs_uri:
            obj = new_obs_uri
        else:
            obj = map.get(obj, obj)
        yield subj, pred, obj, new_graph
