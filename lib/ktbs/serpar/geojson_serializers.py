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
I provide kTBS geojson serializer, this is a serialization with information loss.

http://geojson.org/geojson-spec.html
https://en.wikipedia.org/wiki/GeoJSON
"""
from string import maketrans
import json

from collections import OrderedDict, namedtuple

from rdflib import BNode, Literal, RDF, RDFS, URIRef, XSD
from rdfrest.serializers import register_serializer, SerializeError
from rdfrest.util import coerce_to_uri, wrap_exceptions

from jsonld_serializers import ValueConverter

from ..namespace import KTBS, KTBS_NS_URI
from ..utils import SKOS

GEOJSON = "application/vnd.geo+json"

def create_geodict_structure(gd=None):
    """
    Creates the geojson dictionnary structure.

    :param gd: an empty OrderedDict
    :return: None
    """
    if gd is not None:
        gd['type'] = 'FeatureCollection'
        gd['crs'] = {
                    'type': 'name',
                    'properties': {'name': 'urn:ogc:def:crs:OSG:2:84'}
                    }
        gd['features'] = []


@register_serializer(GEOJSON, "geojson", 85, KTBS.ComputedTraceObsels)
@register_serializer(GEOJSON, "geojson", 85, KTBS.StoredTraceObsels)
@wrap_exceptions(SerializeError)
def serialize_geojson_trace_obsels(graph, tobsels, bindings=None):
    """
    """

    geoObsel = namedtuple('GeoObsel', ['id', 'lat', 'long', 'begin', 'end', 'subject'])

    # TODO : How to manage other coordinates systems ?
    obsels = graph.query("""
        PREFIX : <{0:s}#>
        PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

        SELECT DISTINCT ?obs ?lat ?long ?begin ?end ?subject
        {{
            ?obs :hasTrace [] ;
            geo:long ?long ;
            geo:lat ?lat ;
            :hasBegin ?begin;
            :hasEnd ?end.
            OPTIONAL {{ ?obs :hasSubject ?subject }}
        }}
        ORDER BY ?begin
    """.format(KTBS_NS_URI))

    # geojson export stucture
    geodict = OrderedDict()
    create_geodict_structure(geodict)

    try:
        # Try to set a meaningfull name to the geojson export
        geodict["features"][0]["properties"]["name"] = tobsels.trace.get_label()
    except:
        pass

    for o in map(geoObsel._make, obsels):
        try:
            f = OrderedDict()
            f['type'] = 'Feature'
            f['geometry'] = {'type': 'Point'}
            f['geometry']['coordinates'] = [float(o.lat), float(o.long)]

            f['properties'] = {}
            f['properties']['begin'] = int(o.begin)
            f['properties']['end'] = int(o.end)
            if o.subject is not None:
                f['properties']['subject'] = o.subject

            geodict['features'].append(f)

        except ValueError:
            # Do not keep the point
            # TODO : log an error ?
            pass

    s = json.dumps(geodict)

    yield s
