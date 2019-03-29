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
from pytest import raises as assert_raises

from rdflib import RDF
from rdflib.graph import Graph
from rdflib.term import URIRef

from ktbs.engine.builtin_method import (
    register_builtin_method_impl, unregister_builtin_method_impl)
from ktbs.methods.abstract import AbstractMonosourceMethod
from ktbs.methods.utils import boolean_parameter
from ktbs.namespace import KTBS, KTBS_NS_URI
from rdfrest.cores.factory import unregister_service
from rdfrest.cores.local import LocalCore, Service
from rdfrest.exceptions import CanNotProceedError
from rdfrest.util.config import get_service_configuration

from .test_ktbs_engine import KtbsTestCase

class _ErrorMethod(AbstractMonosourceMethod):
    """I implement the fsa builtin method.
    """
    uri = URIRef('tag:silex.liris.cnrs.fr.2012.08.06.ktbs.test:')

    parameter_types = {
        "fail_trace_description": boolean_parameter,
        "fail_obsels": boolean_parameter,
    }

    def compute_trace_description(self, computed_trace):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.do_compute_obsels
        """
        if computed_trace.get_parameter('fail_trace_description'):
            raise ValueError("failed to compute trace_description")
        else:
            return super(_ErrorMethod, self).compute_trace_description(computed_trace)

    def do_compute_obsels(self, computed_trace, cstate, monotonicity, diag):
        """I implement :meth:`.abstract.AbstractMonosourceMethod.do_compute_obsels
        """
        if computed_trace.get_parameter('fail_obsels'):
            raise ValueError("failed to compute obsels")
        else:
            return

class _ErrorMethodResource(LocalCore):

    RDF_MAIN_TYPE = KTBS.BuiltinMethod

    @classmethod
    def init_service(cls, service):
        uri = _ErrorMethod.uri
        g = Graph()
        g.add((uri, RDF.type, KTBS.BuiltinMethod))
        cls.create(service, uri, g)


class TestMethodErrorHandling(KtbsTestCase):

    def setup(self):
        config = get_service_configuration()
        config.set('server', 'fixed-root-uri', _ErrorMethod.uri)
        self.error_method_service = Service(classes=[_ErrorMethodResource],
                               service_config=config,
                               init_with=_ErrorMethodResource.init_service)
        self.method_impl = _ErrorMethod()
        register_builtin_method_impl(self.method_impl)

        KtbsTestCase.setup(self)

        base = self.base = self.my_ktbs.create_base("b/")
        model = base.create_model("m")
        otype1 = model.create_obsel_type("#ot1")
        otype2 = model.create_obsel_type("#ot2")
        atype = model.create_attribute_type("#at")
        origin = "orig-abc"
        src1 = self.src1 = base.create_stored_trace("s1/", model, origin=origin)

    def teardown(self):
        KtbsTestCase.teardown(self)
        unregister_builtin_method_impl(self.method_impl)
        unregister_service(self.error_method_service)

    def test_unreachable_method(self):
        ctr = self.base.create_computed_trace("ctr/", URIRef('tag:fail'), {},
                                              [self.src1], )

        assert ctr.diagnosis is not None

        with assert_raises(CanNotProceedError):
            ctr.obsels[0]

    def test_fail_trace_description(self):
        ctr = self.base.create_computed_trace("ctr/", _ErrorMethod.uri, {
            "fail_trace_description": True,
        }, [self.src1], )

        assert ctr.diagnosis is not None
        with assert_raises(CanNotProceedError):
            ctr.obsels[0]


    def test_fail_obsels(self):
        ctr = self.base.create_computed_trace("ctr/", _ErrorMethod.uri, {
            "fail_obsels": True,
        }, [self.src1], )

        assert ctr.diagnosis is None
        with assert_raises(CanNotProceedError):
            ctr.obsels[0]



