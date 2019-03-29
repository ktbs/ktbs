#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2017 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
from rdflib import BNode

from ktbs.engine.trace_stats import add_plugin, remove_plugin, NS
from ktbs.namespace import KTBS

def populate_stats(graph, trace):
    # Obsel type statistics
    obsels_graph = trace.obsel_collection.state
    initNs = { '': unicode(KTBS.uri) }
    initBindings = { 'trace': trace.uri }

    count_per_type_result = obsels_graph.query(COUNT_OBSEL_TYPES, initNs=initNs,
                                           initBindings=initBindings)

    if (count_per_type_result is not None and
       len(count_per_type_result.bindings) > 0 and
       len(count_per_type_result.bindings[0]) > 0):

        for res in  count_per_type_result.bindings:
            ot_infos = BNode()

            graph.add((ot_infos, NS.nb, res['nb']))
            graph.add((ot_infos, NS.hasObselType, res['t']))

            graph.add((trace.uri, NS.obselCountPerType, ot_infos))

COUNT_OBSEL_TYPES= '''
    SELECT ?t (count(?o) as ?nb)
        $trace # selected solely to please Virtuoso
    {
        ?o :hasTrace $trace ; a ?t .
    }
    GROUP BY ?t $trace ORDER BY ?t
'''

def start_plugin(_config):
    """I get the configuration values from the main kTBS configuration.

    .. note:: This function is called automatically by the kTBS.
              It is called once when the kTBS starts, not at each request.
    """
    add_plugin(populate_stats)
