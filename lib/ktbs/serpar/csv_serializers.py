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
from rdflib import BNode, Literal, RDF, RDFS, URIRef, XSD
from rdfrest.serializers import register_serializer, SerializeError
from rdfrest.util import coerce_to_uri, wrap_exceptions

from jsonld_serializers import ValueConverter, encode_unicodes

from ..namespace import KTBS, KTBS_NS_URI
from ..utils import SKOS

LEN_KTBS = len(KTBS_NS_URI)+1

CSV = "text/csv"


@register_serializer(CSV, "csv", 85, KTBS.ComputedTraceObsels)
@register_serializer(CSV, "csv", 85, KTBS.StoredTraceObsels)
@wrap_exceptions(SerializeError)
@encode_unicodes
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
            $obs :hasTrace [] ; ?attr [].
        }
    """ % KTBS_NS_URI)

    attr_list = [valconv_uri(attr[0]) for attr in obsels]
    s = u";".join(attr_list)
    yield u"{0}\n".format(s)
