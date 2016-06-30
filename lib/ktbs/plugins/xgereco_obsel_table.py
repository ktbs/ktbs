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
from cgi import escape as cgi_escape
from rdfrest.serializers import register_serializer, SerializeError
from rdfrest.util import wrap_exceptions
from re import compile as Regexp

from ..namespace import KTBS, KTBS_NS_URI
from ..serpar.csv_serializers import iter_csv_rows, LAST_PART

CTYPE = "x-gereco/table"

@wrap_exceptions(SerializeError)
def serialize_obsel_table(graph, resource, bindings=None, highlight=None):

    yield '<html><head><style>'
    yield CSS
    yield '</style><script>'
    yield SCRIPT
    yield '</script></head></body>'
    trace_uri = resource.uri.rsplit('/',1)[0]
    trace_id = trace_uri.rsplit('/',1)[1]
    yield u'<p><a href="{0}/">Trace {1}</a> (<a href="{0}/@obsels.csv" target="_top" download>download as CSV</a>)</p>' \
        .format(trace_uri, trace_id).encode('utf8')

    rows = iter_csv_rows(resource.trace.uri, graph)
    yield '<pre><table><tr>'
    column_headers = next(rows)
    for col_name in column_headers:
        yield u'<th>{}</th>'.format(col_name).encode('utf8')
    for row in rows:
        row_id = row[0].rsplit('/', 1)[1]
        classes = "highlight" if row[0] == highlight else ""
        yield u'</tr><tr id="{}" class="{}">'.format(row_id, classes).encode('utf8')

        for cell in row:
            values = cell.split(' | ')
            htmlvalues = []
            for val in values:
                if HTTP_URI.match(val):
                    short = LAST_PART.search(val).group(1)
                    htmlvalues.append(u'<a href="{0}">{1}</a>'.format(val, short))
                else:
                    htmlvalues.append(cgi_escape(val))

            yield '<td>{}</td>'.format(
              '&nbsp;|&nbsp;'.join(i.encode('utf8') for i in htmlvalues)
            )
    yield '</tr></table></pre>'
    yield '</body></html>'

@wrap_exceptions(SerializeError)
def serialize_obsel_redirect(graph, resource, bindings=None):
    # for the moment, we hijack the obsel representation to represent the whole trace,
    # with the obsel highlighted.

    # A better solution would be to cleanly redirect to @obsels#obsel_id but
    # - the redirection does not work (note that a <script>...</script> written to innerHTML is not executed,
    #   so we can not put scripts in x-gereco/* content-types for the moment
    # - highlight with the :target pseudo-class does not work well in Gereco,
    #   because it messes with window.location

    trace_uri, obsel_id = resource.uri.rsplit('/', 1)
    obsel_collection = resource.factory('{}/@obsels'.format(trace_uri))
    return serialize_obsel_table(obsel_collection.state, obsel_collection, None, resource.uri)


def start_plugin(config):
    register_serializer(CTYPE, None, 50, KTBS.ComputedTraceObsels)(serialize_obsel_table)
    register_serializer(CTYPE, None, 50, KTBS.StoredTraceObsels)(serialize_obsel_table)
    register_serializer(CTYPE, None, 50, KTBS.Obsel)(serialize_obsel_redirect)

HTTP_URI = Regexp('^http(s)?://')
SHORTEN_URI = Regexp('')

CSS = '''

body {
    font-size: 85%;
}

table {
    border-collapse: collapse;
    background-color: lightYellow;
}

th,
td {
    border: 1px solid black;
}

tr:target,
.highlight {
    background-color: lightGreen;
}
'''

SCRIPT = '''
'''
