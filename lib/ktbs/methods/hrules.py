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

import json
from rdflib import Literal, RDF, URIRef, XSD
from rdfrest.util import check_new
from .abstract import AbstractMonosourceMethod, NOT_MON, PSEUDO_MON, STRICT_MON
from .utils import copy_obsel, translate_node
from ..engine.builtin_method import register_builtin_method_impl
from ..namespace import KTBS, KTBS_NS_URI

LOG = logging.getLogger(__name__)

class _HRulesMethod(AbstractMonosourceMethod):
    """I implement the hrules builtin method.
    """
    uri = KTBS.hrules

    parameter_types = {
        "origin": Literal,
        "model": URIRef,
        "rules": json.loads,
    }
    required_parameters = ["model", "rules"]

    def init_state(self, computed_trace, params, cstate, diag):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.init_state
        """
        domains = {}
        src_model = computed_trace.source_traces[0].model
        for atype in src_model.iter_attribute_types():
            dtypes = atype.data_types
            if len(dtypes) == 1:
                domains[unicode(atype.uri)] = dtypes[0]

        rules = params['rules']
        bgps = []
        for rulepos, rule in enumerate(rules):
            if not rule.get('visible', True):
                continue
            new_type = rule["id"]
            for subrule in rule['rules']:
                rank = 0
                bgp = []
                old_type = subrule.get("type", "")
                if old_type:
                    rank += 1000000
                    bgp.append("?obs a <%s>." % old_type)
                for attno, att in enumerate(subrule.get("attributes", ())):
                    rank += 1000
                    if isinstance(att['value'], unicode):
                        dtype = domains.get(att['uri'], XSD.string)
                        value = Literal(att['value'], datatype=dtype)
                    else:
                        dtype = att['value'].get('@datatype', XSD.string)
                        value = Literal(att['value']['@value'], datatype=dtype)
                    att['sparql_value'] = value.n3()
                    if att['operator'] == '==':
                        att['sparql_op'] = '='
                    else:
                        att['sparql_op'] = att['operator']
                    att['var'] = '?att%s' % attno
                    bgp.append('?obs <%(uri)s> %(var)s. '
                               'FILTER(%(var)s %(sparql_op)s %(sparql_value)s).'
                               % att)
                bgp = "".join(bgp)
                rank -= rulepos
                bgps.append([rank, new_type, bgp])
        bgps.sort(reverse=True)

        cstate.update([
            ("bgps", bgps),
            ("last_seen_u", None),
            ("last_seen_b", None),
        ])


    def do_compute_obsels(self, computed_trace, cstate, monotonicity, diag):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.do_compute_obsels
        """
        source = computed_trace.source_traces[0]
        source_obsels = source.obsel_collection
        target_obsels = computed_trace.obsel_collection
        bgps = cstate["bgps"]
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
            LOG.debug("pseudo temporally monotonic %s", computed_trace)
            if last_seen_b is not None:
                begin = last_seen_b - source.get_pseudomon_range()
        else:
            LOG.debug("non-temporally monotonic %s", computed_trace)

        source_uri = source.uri
        target_uri = computed_trace.uri
        source_state = source_obsels.state
        target_contains = target_obsels.state.__contains__
        target_add_graph = target_obsels.add_obsel_graph
        check_new_obs = lambda uri, g=target_obsels.state: check_new(g, uri)

        inserted = set()
        with target_obsels.edit({"add_obsels_only":1}, _trust=True):
            for _rank, new_type, bgp in bgps:
                new_type = URIRef(new_type)
                select = source_obsels.build_select(after=after, bgp=bgp)
                query_str = "PREFIX ktbs: <%s#> %s" % (KTBS_NS_URI, select)
                tuples = list(source_obsels.state.query(query_str))

                for obs_uri, in tuples:
                    new_obs_uri = translate_node(obs_uri, computed_trace,
                                                 source_uri, False)
                    if monotonicity is PSEUDO_MON\
                    and target_contains((new_obs_uri, KTBS.hasTrace, target_uri))\
                    or new_obs_uri in inserted:
                        # could be either because of pseudo-monotony,
                        # or because a BGP with higher priority already matched
                        LOG.debug("--- already seen %s", new_obs_uri)
                        continue # already added

                    new_obs_graph = copy_obsel(obs_uri, computed_trace, source,
                                               new_obs_uri=new_obs_uri,
                                               check_new_obs=check_new_obs,
                    )
                    new_obs_graph.set((new_obs_uri, RDF.type, new_type))
                    target_add_graph(new_obs_graph)
                    inserted.add(new_obs_uri)

        for obs in source.iter_obsels(begin=begin, reverse=True, limit=1):
            # iter only once on the last obsel, if any
            last_seen_u = obs.uri
            last_seen_b = obs.begin

        if last_seen_u is not None:
            last_seen_u = unicode(last_seen_u)
        cstate["last_seen_u"] = last_seen_u
        cstate["last_seen_b"] = last_seen_b

register_builtin_method_impl(_HRulesMethod())
