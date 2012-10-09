# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    RDF-REST is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RDF-REST is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with RDF-REST.  If not, see <http://www.gnu.org/licenses/>.

from nose.tools import raises
from rdflib import URIRef

import example1 # can not import do_tests directly, nose tries to run it...
from example1 import GroupMixin, make_example1_service
from rdfrest.exceptions import RdfRestException
from rdfrest.factory import unregister_service



class TestExample1:

    ROOT_URI = URIRef("http://localhost:11235/foo/")
    service = None
    root = None

    def setUp(self):
        self.service = make_example1_service(self.ROOT_URI)
        self.root = self.service.get(self.ROOT_URI)
        assert isinstance(self.root, GroupMixin)

    def tearDown(self):
        if self.root is not None:
            del self.root
        if self.service is not None:
            unregister_service(self.service)
            del self.service

    def test_embed_trusted_edit(self):
        with self.root.edit(_trust=True):
            with self.root.edit(_trust=True):
                pass

    @raises(RdfRestException)
    def test_embed_untrusted_edit(self):
        with self.root.edit():
            with self.root.edit():
                pass

    @raises(RdfRestException)
    def test_embed_untrusted_trusted_edit(self):
        with self.root.edit():
            with self.root.edit(_trust=True):
                pass

    @raises(RdfRestException)
    def test_embed_trusted_untrusted_edit(self):
        with self.root.edit(_trust=True):
            with self.root.edit():
                pass

    def test_example1(self):
        """I use the comprehensive test sequence defined in example1.py"""
        example1.do_tests(self.root)

