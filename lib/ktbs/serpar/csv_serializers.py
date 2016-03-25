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
        csvw.writerow([ i.encode('utf-8') for i in row ])
        # immediately yield each line
        yield sio.getvalue()
        # then empty sio before writing next line
        sio.reset()
        sio.truncate()

def iter_csv_rows(trace_uri, graph, sep=u' | '):
    """
    Convert obsels in graph to a tabular form, an iterable of unicode strings.

    NB: the first yielded table contains column names.
    """

    results0 = graph.query("""
        PREFIX : <{0}#>
        SELECT DISTINCT ?attr
        {{
            ?obs :hasTrace <{1}> ; ?attr [].
        }}
    """.format(KTBS_NS_URI, trace_uri))

    if len(results0) == 0:
        # no obsel, yield minimal column header and stop
        yield [u'id', u'type', u'begin', u'end']
        return

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

    # yielding column headers
    yield ['id'] + vars

    select_parts = []
    where_parts = []
    for var, prop in zip(vars, props):
        select_parts.append(u'?{0}'
                         .format(var))
        where_parts.append(u'OPTIONAL {{ ?id <{0}> ?{1} }}'
                         .format(prop, var))

    obs_query = u"""SELECT ?id {0}
            WHERE {{
                ?id <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> <{1}> .
                {2}
            }}
            ORDER BY ?end ?begin ?id
    """.format(' '.join(select_parts),
               trace_uri,
               '\n'.join(where_parts))

    results = graph.query(obs_query)
    for obsel_id, tuples in groupby(results, lambda tpl: tpl[0]):
        sets = [ set() for i in vars ]
        for tuple in tuples:
            for val, valset in zip(tuple[1:], sets):
                if val is not None:
                    valset.add(val)
        yield [obsel_id] + [ sep.join(valset) for valset in sets ]


def make_var_name(uri, vars):
    """
    Convert a property URI to a SPARQL variable name.

    :param uri: the property URI
    :type uri: unicode string
    :param vars: the variables already in use (to prevent clashes)
    :type vars: iterable of unicode strings
    """

    # make a short, SPARQL-safe name from URI
    var_name = LAST_PART.search(uri).group(1)
    if HAS_HAS.match(var_name):
        if var_name[3] in ['_', '-']:
            var_name = var_name[4:]
        else:
            var_name = ''.join((var_name[3].lower(), var_name[4:]))
    var_name = UNAUTHORIZED.sub('_', var_name)

    if var_name in vars:
        i = 2
        while True:
            attempt = u'{}{}'.format(var_name, i)
            if attempt not in vars:
                var_name = attempt
                break
            i += 1

    return var_name

LAST_PART = Regexp(r'([^#/]+)[#/]?$')
HAS_HAS = Regexp(r'^has[A-Z_-]')
UNAUTHORIZED = Regexp(r'[^0-9A-Za-z_]')