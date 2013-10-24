# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
#    GNU Lesser General Public License for more .
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with KTBS.  If not, see <http://www.gnu.org/licenses/>.

from nose.tools import assert_equal, assert_raises, eq_

from rdflib import BNode, Graph, Literal, RDF, RDFS, URIRef

from rdfrest.exceptions import CanNotProceedError, InvalidDataError, \
    MethodNotAllowedError, RdfRestException

from ktbs.namespace import KTBS
from ktbs.plugins.jsonld import parse_jsonld

from .test_ktbs_engine import KtbsTestCase

class TestJsonBase(KtbsTestCase):

    def test_valid_post_base(self):
        """Process the json parsing of a valid base creation.
        """

        request = """{
            "@id": "b1/",
            "@type": "Base"
        }"""

        # The resource should be the kTBS root for a base
        resource = self.my_ktbs
        charset = "UTF-8"
        graph = parse_jsonld(request, resource.uri, charset)

        created_resources = resource.post_graph(graph, None)

        eq_ (len(created_resources), 1)

class TestJsonTrace(KtbsTestCase):

    def setUp(self):
        KtbsTestCase.setUp(self)
        self.base = self.my_ktbs.create_base(id="BaseTest/", label="Test base")

    def test_valid_post_trace(self):
        """Process the json parsing of a valid trace creation.
        """

        # TODO mettre l'origine à la date-heure actuelle
        request = """{
            "@id": "t1/",
            "@type": "StoredTrace",
            "label": "My new trace",
            "hasModel": "http://liris.cnrs.fr/silex/2011/simple-trace-model",
            "origin": "2013-10-23T18:00:00.000000",
            "hasDefaultSubject": "Unit testing"
        }"""

        # The resource should be the kTBS root for a base
        resource = self.base
        charset = "UTF-8"
        graph = parse_jsonld(request, resource.uri, charset)

        created_resources = resource.post_graph(graph, None)

        eq_ (len(created_resources), 1)
