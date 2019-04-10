#!/usr/bin/env python
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
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with KTBS.  If not, see <http://www.gnu.org/licenses/>.

"""
Nose unit-testing for the kTBS model client API.
"""
from unittest import skip
from pytest import raises as assert_raises

from rdflib import URIRef, XSD

from rdfrest.exceptions import InvalidDataError

from ktbs.engine.service import make_ktbs
from ktbs.namespace import KTBS

from utest.test_ktbs_engine import KtbsTestCase

KTBS_ROOT = "http://localhost:12345/"

class _TestIterObselsMixin(object):

    def test_no_param(self):
        assert self.obsels == self.t.list_obsels()

    def test_begin(self):
        assert self.obsels[2:] == self.t.list_obsels(begin=15)

    def test_end(self):
        assert self.obsels[:5] == self.t.list_obsels(end=45)

    def test_after_obsel(self):
        assert self.obsels[3:] == self.t.list_obsels(after=self.o2)

    def test_after_uri(self):
        assert self.obsels[3:] == self.t.list_obsels(after=self.o2.uri)

    def test_before_obsel(self):
        assert self.obsels[:3] == self.t.list_obsels(before=self.o3)

    def test_before_uri(self):
        assert self.obsels[:3] == self.t.list_obsels(before=self.o3.uri)

    def test_reverse(self):
        assert self.obsels[::-1] == self.t.list_obsels(reverse=True)

    def test_bgb_single_type(self):
        bgp = """
            ?obs a m:OT2.
        """
        assert [self.o0, self.o2, self.o4] == self.t.list_obsels(bgp=bgp)

    def test_bgb_filter(self):
        bgp = """
            ?obs m:OT1-at1 ?at1 ; m:OT1-at2 ?at2.
            FILTER(?at1 > ?at2)
        """
        assert [self.o0, self.o3] == self.t.list_obsels(bgp=bgp)

    def test_bgp_timestamps(self):
        bgp = """
            FILTER(?e < (?b+40))
        """
        assert self.obsels == self.t.list_obsels(bgp=bgp)

    def test_limit(self):
        assert self.obsels[:1] == self.t.list_obsels(limit=1)
        assert self.obsels[:3] == self.t.list_obsels(limit=3)
        assert self.obsels == self.t.list_obsels(limit=len(self.obsels)+1)

    def test_limit_offset(self):
        assert self.obsels[1:2] == self.t.list_obsels(limit=1, offset=1)
        assert self.obsels[2:4] == self.t.list_obsels(limit=2, offset=2)

    def test_limit_reverse(self):
        assert self.obsels[-1:] == self.t.list_obsels(reverse=True, limit=1)

    def test_multiple_params(self):
        bgp = """
            ?obs a m:OT2.
        """
        assert [self.o4, self.o2] == \
            self.t.list_obsels(begin=5, end=45, reverse=True, bgp=bgp)

class TestIterObsels(_TestIterObselsMixin, KtbsTestCase):

    def setup(self):
        KtbsTestCase.setup(self)
        self.b = self.my_ktbs.create_base("b/")
        self.m = self.b.create_model("m")
        self.ot1 = self.m.create_obsel_type("#OT1")
        self.ot1at1 = self.m.create_attribute_type("#OT1-at1")
        self.ot1at2 = self.m.create_attribute_type("#OT1-at2")
        self.ot1at3 = self.m.create_attribute_type("#OT1-at3")
        self.ot2 = self.m.create_obsel_type("#OT2", [self.ot1])
        self.t = self.b.create_stored_trace("t1/", self.m, "some_time", default_subject="alice")

        self.o0 = self.t.create_obsel("o0", self.ot2, 00, attributes={
            self.ot1at1: 0o3,
            self.ot1at2: 0o2,
        })
        self.o1 = self.t.create_obsel("o1", self.ot1, 10, attributes={
            self.ot1at1: 101,
            self.ot1at2: 102,
            self.ot1at3: 103,
        })
        self.o2 = self.t.create_obsel("o2", self.ot2, 20, attributes={
            self.ot1at1: 201,
            self.ot1at2: 202,
            self.ot1at3: 203,
        })
        self.o3 = self.t.create_obsel("o3", self.ot1, 30, attributes={
            self.ot1at1: 303,
            self.ot1at2: 302,
            self.ot1at3: 301,
        })
        self.o4 = self.t.create_obsel("o4", self.ot2, 40, attributes={
            self.ot1at1: 401,
            self.ot1at2: 402,
            self.ot1at3: 403,
        })
        self.o5 = self.t.create_obsel("o5", self.ot1, 50, attributes={
            self.ot1at1: 501,
            self.ot1at2: 502,
        })
        self.obsels = [ self.o0, self.o1, self.o2, self.o3, self.o4, self.o5]

    def teardown(self):
        self.t.delete()
        self.m.delete()
        self.b.delete()
        KtbsTestCase.teardown(self)


class TestIterObselsDuration(_TestIterObselsMixin, KtbsTestCase):

    def setup(self):
        KtbsTestCase.setup(self)
        self.b = self.my_ktbs.create_base("b/")
        self.m = self.b.create_model("m")
        self.ot1 = self.m.create_obsel_type("#OT1")
        self.ot1at1 = self.m.create_attribute_type("#OT1-at1")
        self.ot1at2 = self.m.create_attribute_type("#OT1-at2")
        self.ot1at3 = self.m.create_attribute_type("#OT1-at3")
        self.ot2 = self.m.create_obsel_type("#OT2", [self.ot1])
        self.t = self.b.create_stored_trace("t1/", self.m, "some_time", default_subject="alice")

        self.o0 = self.t.create_obsel("o0", self.ot2, 00, 30, attributes={
            self.ot1at1: 0o3,
            self.ot1at2: 0o2,
        })
        self.o1 = self.t.create_obsel("o1", self.ot1, 10, 30, attributes={
            self.ot1at1: 101,
            self.ot1at2: 102,
            self.ot1at3: 103,
        })
        self.o2 = self.t.create_obsel("o2", self.ot2, 20, 30, attributes={
            self.ot1at1: 201,
            self.ot1at2: 202,
            self.ot1at3: 203,
        })
        self.o3 = self.t.create_obsel("o3", self.ot1, 20, 30, attributes={
            self.ot1at1: 303,
            self.ot1at2: 302,
            self.ot1at3: 301,
        })
        self.o4 = self.t.create_obsel("o4", self.ot2, 20, 40, attributes={
            self.ot1at1: 401,
            self.ot1at2: 402,
            self.ot1at3: 403,
        })
        self.o5 = self.t.create_obsel("o5", self.ot1, 20, 50, attributes={
            self.ot1at1: 501,
            self.ot1at2: 502,
        })
        self.obsels = [ self.o0, self.o1, self.o2, self.o3, self.o4, self.o5]

    def teardown(self):
        self.t.delete()
        self.m.delete()
        self.b.delete()
        KtbsTestCase.teardown(self)

