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

from ktbs.namespace import KTBS

from .test_ktbs_engine import KtbsTestCase


class TestOverrideParameter(KtbsTestCase):

    def setup(self):
        super(TestOverrideParameter, self).setup()
        self.base = self.my_ktbs.create_base("b/")
        model = self.base.create_model("m")
        otype1 = self.otype1 = model.create_obsel_type("#ot1")
        otype2 = self.otype2 = model.create_obsel_type("#ot2")
        src = self.base.create_stored_trace("s/", model, origin="now")
        src.create_obsel(None, otype1)
        src.create_obsel(None, otype2)
        src.create_obsel(None, otype2)
        self.meth1 = self.base.create_method("meth1", KTBS.filter,
                                            {"otypes": otype1.uri})
        self.ctr = self.base.create_computed_trace("ctr/", self.meth1,
                                                   sources=[src])

    def test_overriden_parameter_in_computed_trace(self):
        assert len(self.ctr.obsels) == 1
        self.ctr.set_parameter("otypes", self.otype2.uri)
        assert len(self.ctr.obsels) == 2
        self.ctr.set_parameter("otypes", None)
        assert len(self.ctr.obsels) == 1
        # deleting it a second time should have no effect
        self.ctr.set_parameter("otypes", None)
        assert len(self.ctr.obsels) == 1

    def test_overriden_parameter_in_method(self):
        meth2 = self.base.create_method("meth2", self.meth1,
                                            {"otypes": self.otype2.uri})
        self.ctr.method = meth2
        assert len(self.ctr.obsels) == 2
        self.ctr.set_parameter("otypes", self.otype1.uri)
        assert len(self.ctr.obsels) == 1
        meth2.set_parameter("otypes", None)
        assert len(self.ctr.obsels) == 1
        meth2.set_parameter("otypes", self.otype2.uri)
        assert len(self.ctr.obsels) == 1
        self.ctr.set_parameter("otypes", None)
        assert len(self.ctr.obsels) == 2
        meth2.set_parameter("otypes", None)
        assert len(self.ctr.obsels) == 1
