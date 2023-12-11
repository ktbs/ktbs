# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2015 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
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
#    RDF-REST is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

"""
Nose unit-testing for the kTBS geojson serialization part.
"""
from collections import OrderedDict, namedtuple
import json

from rdflib import URIRef

from ktbs.namespace import KTBS
from ktbs.serpar.geojson_serializers import serialize_geojson_trace_obsels, create_geodict_structure

from .test_ktbs_engine import KtbsTestCase

class TestGeojsonObselsSerialization(KtbsTestCase):

    def setup_method(self):
        super(TestGeojsonObselsSerialization, self).setup_method()
        self.base = self.my_ktbs.create_base("b1/")
        self.model = self.base.create_model("modl",)
        self.ot1 = ot1 = self.model.create_obsel_type("#OT1")
        self.model.set_unit(KTBS.sequence)
        #self.lat = self.model.create_attribute_type(URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#lat"), ot1)
        #self.long = self.model.create_attribute_type(URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#long"), ot1)
        self.t1 = self.base.create_stored_trace("t1/", self.model, "Origine opaque")

    def teardown_method(self):
        super(TestGeojsonObselsSerialization, self).teardown_method()
        self.base = None
        self.model = self.ot1 = self.lat = self.long = None
        self.t1 = None

    def populate(self):
        # create obsel in wrong order, to check that they are serialized in
        # the correct order nonetheless
        self.geoList = []

        geoObsel = namedtuple('GeoObsel', ['id', 'lat', 'long', 'begin', 'end', 'subject'])
        self.geoList.append(geoObsel('o1', 45.8100, 4.8291, 1, 1, 'foo'))
        self.geoList.append(geoObsel('o2', 45.8026, 4.6217, 2, 2, 'bar'))
        self.geoList.append(geoObsel('o3', 45.8156, 4.7853, 3, 3, 'baz'))

        for o in self.geoList[::-1]:
            setattr(self,
                    '{0}'.format(o.id),
                    self.t1.create_obsel('{0}'.format(o.id),
                                         self.ot1,
                                         o.begin,
                                         o.end,
                                         o.subject,
                                         {URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#lat"): o.lat,
                                          URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#long"): o.long}))

    def test_populated_obsels(self):
        self.populate()
        geodict = OrderedDict()
        create_geodict_structure(geodict)
        for o in self.geoList[::1]:
            f = OrderedDict()
            f['type'] = 'Feature'
            f['geometry'] = {'type': 'Point'}
            f['geometry']['coordinates'] = [o.lat, o.long]

            f['properties'] = {}
            f['properties']['begin'] = o.begin
            f['properties']['end'] = o.end
            if o.subject is not None:
                f['properties']['subject'] = o.subject

            geodict['features'].append(f)
        geoRefSerialized = json.dumps(geodict)

        geojsoncontent = serialize_geojson_trace_obsels(self.t1.obsel_collection.state, self.t1.obsel_collection)

        res = "".join(geojsoncontent)

        assert res == geoRefSerialized
