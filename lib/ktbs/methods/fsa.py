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
Implementation of the fsa builtin methods.
"""
import logging

import json

from fsa4streams import FSA
from fsa4streams.matcher import DIRECTORY as matcher_directory
from rdflib import Literal, RDF, URIRef, Graph
from rdfrest.util import check_new
from .abstract import AbstractMonosourceMethod, NOT_MON, PSEUDO_MON, STRICT_MON
from .utils import translate_node
from ..engine.builtin_method import register_builtin_method_impl
from ..namespace import KTBS
from ..time import get_converter_to_unit, lit2datetime #pylint: disable=E0611

# pylint is confused by a module named time (as built-in module)

LOG = logging.getLogger(__name__)

def match_obseltype(transition, event, token, fsa):
    """
    The 'obseltype' matcher.

    With this matcher,
    transition conditions are interpreted as obseltype URIs.
    """
    triple = (
        URIRef(event),
        RDF.type,
        URIRef(transition['condition'], fsa.source.model_uri)
    )
    return triple in fsa.source_obsels_graph

matcher_directory['obseltype'] = match_obseltype

def match_sparql_ask(transition, event, token, fsa):
    """
    The 'sparql-ask' matcher.

    With this matcher,
    transition conditions are interpreted as the WHERE clause of a SPARQL Ask query,
    where variable ?obs is bound to the considered obsel,
    and prefix m: is bound to the source trace URI.
    """
    m_ns = fsa.source.model_uri
    if m_ns[-1] != '/' and m_ns[-1] != '#':
        m_ns += '#'
    history = token and token.get('history_events')
    if history:
        pred = URIRef(history[-1])
    else:
        pred = None
    return fsa.source_obsels_graph.query(
        "ASK { %s }" % transition['condition'],
        initNs={"m": m_ns},
        initBindings={"?obs": URIRef(event), "?pred": pred},
    ).askAnswer

matcher_directory['sparql-ask'] = match_sparql_ask



class _FSAMethod(AbstractMonosourceMethod):
    """I implement the fsa builtin method.
    """
    uri = KTBS.fsa

    parameter_types = {
        "origin": Literal,
        "model": URIRef,
        "fsa": FSA.from_str,
    }
    required_types = ["fsa"]

    def init_state(self, computed_trace, params, cstate, diag):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.init_state
        """
        cstate.update([
            ("fsa", params.get("fsa").export_structure_as_dict()),
            ("tokens", None),
            ("last_seen", None),
        ])


    def do_compute_obsels(self, computed_trace, cstate, monotonicity, diag):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.do_compute_obsels
        """
        source = computed_trace.source_traces[0]
        source_obsels = source.obsel_collection
        target_obsels = computed_trace.obsel_collection
        last_seen = cstate["last_seen"]
        if last_seen is not None:
            last_seen = source.service.get(URIRef(last_seen))

        fsa = FSA(cstate['fsa'], False) # do not check structure again
        if fsa.default_matcher is None:
            #fsa.default_matcher = "obseltype"              # <- doesn't work in fsa4streams v0.4
            fsa._structure['default_matcher'] = "obseltype" # <- workaround
        fsa.source = source
        fsa.target = computed_trace
        fsa.source_obsels_graph = source_obsels.state

        if monotonicity is STRICT_MON:
            LOG.debug("strictly temporally monotonic %s, reloading state", computed_trace)
            tokens = cstate['tokens']
            if tokens:
                fsa.load_tokens_from_dict(tokens)
        else:
            LOG.debug("NOT strictly temporally monotonic %s, restarting", computed_trace)
            passed_maxtime = False
            last_seen = None
            target_obsels._empty() # friend #pylint: disable=W0212

        source_uri = source.uri
        source_state = source_obsels.state
        source_value = source_state.value
        target_uri = computed_trace.uri
        target_model_uri = computed_trace.model_uri
        target_add_graph = target_obsels.add_obsel_graph

        with target_obsels.edit({"add_obsels_only":1}, _trust=True):
            for obs in source.iter_obsels(after=last_seen, refresh="no"):
                last_seen = obs
                event = unicode(obs.uri)
                matching_tokens = fsa.feed(event)
                for i, token in enumerate(matching_tokens):
                    source_obsels = [ URIRef(uri) for uri in token['history_events']]
                    otype_uri = URIRef(token['state'], target_model_uri)
                    LOG.debug("matched {} -> {}".format(source_obsels[-1], otype_uri))

                    new_obs_uri = translate_node(source_obsels[-1], computed_trace,
                                                 source_uri, False)
                    if i > 0:
                        new_obs_uri = URIRef("{}-{}".format(new_obs_uri, i))
                    new_obs_graph = Graph()
                    new_obs_add = new_obs_graph.add
                    new_obs_add((new_obs_uri, KTBS.hasTrace, target_uri))
                    new_obs_add((new_obs_uri, RDF.type, otype_uri))
                    new_obs_add((new_obs_uri, KTBS.hasBegin, source_value(source_obsels[0], KTBS.hasBegin)))
                    new_obs_add((new_obs_uri, KTBS.hasEnd, source_value(source_obsels[-1], KTBS.hasEnd)))
                    for source_obsel in source_obsels:
                        new_obs_add((new_obs_uri, KTBS.hasSourceObsel, source_obsel))

                    target_add_graph(new_obs_graph)

        cstate["last_seen"] = last_seen and unicode(last_seen.uri)
        cstate["tokens"] = fsa.export_tokens_as_dict()

register_builtin_method_impl(_FSAMethod())
