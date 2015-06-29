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
from string import maketrans

from rdflib import BNode, Literal, RDF, RDFS, URIRef, XSD
from rdfrest.serializers import register_serializer, SerializeError
from rdfrest.util import coerce_to_uri, wrap_exceptions

from jsonld_serializers import ValueConverter

from ..namespace import KTBS, KTBS_NS_URI
from ..utils import SKOS

LEN_KTBS = len(KTBS_NS_URI)+1

CSV = "text/csv"

@register_serializer(CSV, "csv", 85, KTBS.ComputedTraceObsels)
@register_serializer(CSV, "csv", 85, KTBS.StoredTraceObsels)
@wrap_exceptions(SerializeError)
def serialize_csv_trace_obsels(graph, tobsels, bindings=None):

    trace_uri = tobsels.trace.uri
    model_uri = tobsels.trace.model_uri
    if model_uri[-1] not in { "/", "#" }:
        model_uri += "#"
    valconv = ValueConverter(trace_uri, { model_uri: "m" })
    valconv_uri = valconv.uri

    obsels = graph.query("""
        PREFIX : <%s#>
        SELECT DISTINCT ?attr
        {
            ?obs :hasTrace [] ; ?attr [].
        }
    """ % KTBS_NS_URI)

    # Build meaningfull sparql variables without special chars
    all_attr = {}
    intab = u'#:'
    outtab = u'_'
    # maketrans(intab, outtab) does not work with unicode
    transtab = dict((ord(char), u'_') for char in intab)
    for attr in obsels:
        abr = None

        # TODO do a clean thing for type
        if attr[0].find("22-rdf-syntax-ns#type") != -1:
            abr = "type"
        else:
            # TODO Dirty hack to remove hasTrace attribute : improve
            if attr[0].find("ktbs#hasTrace") == - 1:
                abr = valconv_uri(attr[0]).translate(transtab)

        if abr is not None:
            if all_attr.get(abr) is None:
                all_attr[abr] = attr[0]

            # TODO : at least a warning if we have several variables with
            # the same name
            #else:
            #    raise Something
        
        #yield u"{0} : {1}\n".format(abr, attr[0]).encode('utf-8)

    opt_attr = []
    for abr, attr in all_attr.items():
        opt_attr.append(u'OPTIONAL {{ ?id <{0}> ?{1} }}'.format(attr, abr))

    all_opts = u'\n\t'.join(opt_attr)

    header = u' '.join(['?{0}'.format(abr) for abr in all_attr.keys()])

    obs_query = u"""SELECT {0}
            {{
                ?id <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> [] .
                  {1}
            }} ORDER BY ?hasEnd ?hasBegin""".format(header, all_opts)

    obsels = graph.query(obs_query)

    s = obsels.serialize(format='csv', encoding='utf-8')
    yield s
