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
from rdfrest.util import check_new
from .abstract import AbstractMonosourceMethod, NOT_MON, PSEUDO_MON, STRICT_MON
from .utils import translate_node
from ..engine.builtin_method import register_builtin_method_impl
from ..namespace import KTBS, KTBS_NS_URI

# pylint is confused by a module named time (as built-in module)

LOG = logging.getLogger(__name__)

class _ISparqlMethod(AbstractMonosourceMethod):
    """I implement the filter builtin method.
    """
    uri = KTBS.isparql

    parameter_types = {
        "origin": Literal,
        "model": URIRef,
        "sparql": unicode,
    }

    def init_state(self, computed_trace, params, cstate, diag):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.init_state
        """
        params2 = dict(params)
        sparql = params2.pop('sparql')
        if not "%(__subselect__)s" in sparql:
            raise ValueError(
                "sparql parameter must include '%(__subselect__)s' placeholder")
        params2['__subselect__'] = "{%(__subselect__)s}"
        sparql %= params2
        sparql = "PREFIX ktbs: <%s#> %s" % (KTBS_NS_URI, sparql)

        cstate.update([
            ("sparql", sparql),
            ("last_seen_u", None),
            ("last_seen_b", None),
        ])


    def do_compute_obsels(self, computed_trace, cstate, monotonicity, diag):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.do_compute_obsels
        """
        source = computed_trace.source_traces[0]
        source_obsels = source.obsel_collection
        target_obsels = computed_trace.obsel_collection
        last_seen_u = cstate["last_seen_u"]
        if last_seen_u:
            last_seen_u = URIRef(last_seen_u)
        last_seen_b = cstate["last_seen_b"]

        begin = None
        after = None
        if monotonicity is NOT_MON:
            LOG.debug("non-monotonic %s", computed_trace)
            last_seen_u = last_seen_b = None
            target_obsels._empty() # friend #pylint: disable=W0212
        elif monotonicity is STRICT_MON:
            LOG.debug("strictly temporally monotonic %s", computed_trace)
            if last_seen_u:
                after = last_seen_u
        elif monotonicity is PSEUDO_MON:
            LOG.debug("pseudo-monotonic %s", computed_trace)
            if last_seen_b is not None:
                begin = last_seen_b - source.get_pseudomon_range()
        else:
            LOG.debug("add-monotonic %s", computed_trace)
        subselect = source_obsels.build_select(
            begin=begin, after=after, selected=
            "(?obs as ?sourceObsel) (?b as ?sourceBegin) (?e as ?sourceEnd)")
        sparql = cstate['sparql'] % {'__subselect__': subselect}

        rows = source_obsels.get_state({'refresh': 'no'}).query(sparql)
        columns = [ unicode(i) for i in rows.vars ]
        if 'sourceObsel' not in columns:
            raise Exception("no ?sourceObsel in the SPARQL result")
        if 'begin' not in columns:
            raise Exception("no ?begin in the SPARQL result")
        if 'type' not in columns:
            raise Exception("no ?type in the SPARQL result")
        if 'end' not in columns:
            # let's add end(=begin) to the results
            i_begin = columns.index('begin')
            rows = ( list(row) + [row[i_begin]] for row in rows )
            columns.append('end')
        i_sourceObsel = columns.index('sourceObsel')
        columns = [ var2predicate(i, computed_trace.model_uri) for i in columns ]

        source_uri = source.uri
        target_uri = computed_trace.uri
        target_contains = target_obsels.state.__contains__
        target_add_graph = target_obsels.add_obsel_graph
        with target_obsels.edit({"add_obsels_only":1}, _trust=True):
            for row in rows:
                sourceObsel = row[i_sourceObsel]

                new_obs_uri = translate_node(sourceObsel, computed_trace,
                                             source_uri, False)
                if monotonicity is not STRICT_MON\
                and target_contains((new_obs_uri, KTBS.hasTrace, target_uri)):
                    LOG.debug("--- already seen %s", new_obs_uri)
                    continue # already added

                LOG.debug("--- transforming %s", sourceObsel)
                new_obs_graph = Graph()
                add = new_obs_graph.add
                add((new_obs_uri, KTBS.hasTrace, target_uri))
                for pred, obj in zip(columns, row):
                    if obj is not None:
                        add((new_obs_uri, pred, obj))
                target_add_graph(new_obs_graph)

        for obs in source.iter_obsels(begin=begin, reverse=True, limit=1):
            # iter only once on the last obsel, if any
            last_seen_u = obs.uri
            last_seen_b = obs.begin

        cstate["last_seen_u"] = last_seen_u
        cstate["last_seen_b"] = last_seen_b

_VAR2PRED = {
    'type': RDF.type,
    'begin': KTBS.hasBegin,
    'end': KTBS.hasEnd,
    'beginDT': KTBS.hasBeginDT,
    'endDT': KTBS.hasEndDT,
    'subject': KTBS.hasSubject,
    'sourceObsel': KTBS.hasSourceObsel,
    # the keys are not stricly required (see var2predicate() below)
    # but should slightly improve performances
    'sourceObsel1': KTBS.hasSourceObsel,
    'sourceObsel2': KTBS.hasSourceObsel,
    'sourceObsel3': KTBS.hasSourceObsel,
}
def var2predicate(varname, model_uri):
    """
    Convert a SPARQL variable to the appropriate predicate.
    """
    varname = unicode(varname)
    predicate = _VAR2PRED.get(varname)
    if predicate is None:
        if varname.startswith('sourceObsel'):
            predicate = KTBS.hasSourceObsel
        else:
            predicate = URIRef('#%s' % varname, model_uri)
    return predicate


register_builtin_method_impl(_ISparqlMethod())
