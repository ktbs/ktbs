#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2015 Francoise Conil <fconil@liris.cnrs.fr> /
#    Universite de Lyon, CNRS <http://www.universite-lyon.fr>
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
I provide kTBS CSV serializer, this is a serialization with information loss.
"""
from cStringIO import StringIO
from csv import writer as csv_writer
from itertools import groupby
from rdflib import RDF
from rdfrest.serializers import register_serializer, SerializeError
from rdfrest.util import wrap_exceptions
from re import compile as Regexp

from ..namespace import KTBS, KTBS_NS_URI

LEN_KTBS = len(KTBS_NS_URI)+1

CSV = "text/csv"

@register_serializer(CSV, "csv", 85, KTBS.ComputedTraceObsels)
@register_serializer(CSV, "csv", 85, KTBS.StoredTraceObsels)
@wrap_exceptions(SerializeError)
def serialize_csv_trace_obsels(graph, resource, bindings=None):
    sio = StringIO()
    csvw = csv_writer(sio)
    for row in iter_csv_rows(resource.trace.uri, graph):
        csvw.writerow(row)
        yield sio.getvalue()
        sio.reset()
        sio.truncate()

def iter_csv_rows(trace_uri, graph, sep=u' | '):

    results0 = graph.query("""
        PREFIX : <{0}#>
        SELECT DISTINCT ?attr
        {{
            ?obs :hasTrace <{1}> ; ?attr [].
        }}
    """.format(KTBS_NS_URI, trace_uri))

    ktbs_props = [ i[0] for i in results0 if i[0].startswith(KTBS.uri) ]
    other_props = [ i[0] for i in results0 if not i[0].startswith(KTBS.uri) ]
    ktbs_props.sort()
    other_props.sort()

    ktbs_props.remove(KTBS.hasTrace)
    if KTBS.hasSourceObsel in ktbs_props:
        ktbs_props.remove(KTBS.hasSourceObsel)
        src_obs = [ KTBS.hasSourceObsel ]
    else:
        src_obs = []

    other_props.remove(RDF.type)

    props = [RDF.type] + ktbs_props + other_props + src_obs
    vars = []
    for prop in props:
        vars.append(make_var_name(prop, vars))

    yield ['id'] + [ i.encode('utf8') for i in vars ]

    sel_parts = []
    bgp_parts = []
    for var, prop in zip(vars, props):
        sel_parts.append(u'?{0}'
                         .format(var))
        bgp_parts.append(u'OPTIONAL {{ ?id <{1}> ?{0} }}'
                         .format(var, prop))

    obs_query = u"""SELECT ?id {0}
            WHERE {{
                ?id <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> <{1}> .
                {2}
            }}
            ORDER BY ?end ?begin ?id
    """.format(' '.join(sel_parts),
               trace_uri,
               '\n'.join(bgp_parts))

    for obs, tuples in groupby(graph.query(obs_query), lambda tpl: tpl[0]):
        sets = [ set() for i in vars ]
        for tuple in tuples:
            for val, valset in zip(tuple[1:], sets):
                if val is not None:
                    valset.add(val)
        yield [obs.encode('utf8')] + [ sep.join(valset).encode('utf8') for valset in sets ]


def make_var_name(uri, vars):
    var_name = LAST_PART.search(uri).group(1)
    if HAS_VERB.match(var_name):
        if var_name[3] == '_':
            var_name = var_name[4:]
        else:
            var_name = ''.join((var_name[3].lower(), var_name[4:]))

    if var_name in vars:
        i = 2
        while True:
            attempt = u'{}{}'.format(var_name, i)
            if attempt not in vars:
                var_name = attempt
                break
            i = i+1

    return var_name

LAST_PART = Regexp(r'([^#/]+)/?$')
HAS_VERB = Regexp(r'^has[A-Z_]')