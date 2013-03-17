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

from datetime import datetime, timedelta
from nose.tools import assert_equal, assert_raises, eq_
from rdflib import BNode, Graph, Literal, RDF, RDFS, URIRef
from rdfrest.exceptions import CanNotProceedError, InvalidDataError, \
    MethodNotAllowedError, RdfRestException
from rdfrest.factory import unregister_service
from rdfrest.local import StandaloneResource
from rdfrest.http_client import HttpResource
from rdfrest.http_server import HttpFrontend
from rdfrest.iso8601 import UTC
from threading import Thread
from time import sleep
from wsgiref.simple_server import make_server

from ktbs.api.ktbs_root import KtbsRootMixin
from ktbs.engine.resource import METADATA
from ktbs.engine.service import make_ktbs
from ktbs.methods.filter import LOG as FILTER_LOG
from ktbs.namespace import KTBS
from ktbs.time import lit2datetime

from .utils import StdoutHandler

cmdline = "echo"

class KtbsTestCase(object):

    my_ktbs = None
    service = None

    def setUp(self):
        self.my_ktbs = make_ktbs("http://localhost:12345/")
        self.service = self.my_ktbs.service

    def tearDown(self):
        if self.service is not None:
            unregister_service(self.service)
            self.service = None
        if self.my_ktbs is not None:
            self.my_ktbs = None

class HttpKtbsTestCaseMixin(object):
    """A mixin class to be mixed to KtbsTestCase to publish as HTTP service.

    Note that this adds an 'http' property to the object.
    """

    httpd = None

    def setUp(self):
        super(HttpKtbsTestCaseMixin, self).setUp()
        app = HttpFrontend(self.service, cache_control="max-age=60")
        httpd = make_server("localhost", 12345, app,
                            handler_class=StdoutHandler)
        thread = Thread(target=httpd.serve_forever)
        thread.start()
        self.httpd = httpd

        self.my_ktbs = HttpResource.factory("http://localhost:12345/")
        assert isinstance(self.my_ktbs, KtbsRootMixin)

    def tearDown(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd = None
        super(HttpKtbsTestCaseMixin, self).tearDown()


class TestKtbs(KtbsTestCase):

    def test_post_bad_type_to_root(self):
        graph = Graph()
        created = BNode()
        graph.add((self.my_ktbs.uri, KTBS.hasBase, created))
        graph.add((created, RDF.type, RDFS.Resource))
        with assert_raises(RdfRestException):
            self.my_ktbs.post_graph(graph)

    def test_post_no_type_to_root(self):
        graph = Graph()
        created = BNode()
        graph.add((self.my_ktbs.uri, RDFS.seeAlso, created))
        graph.add((created, RDF.type, KTBS.Base))
        with assert_raises(RdfRestException):
            self.my_ktbs.post_graph(graph)

    def test_post_bad_type_to_base(self):
        graph = Graph()
        created = BNode()
        graph.add((self.my_ktbs.uri, KTBS.contains, created))
        graph.add((created, RDF.type, RDFS.Resource))
        with assert_raises(RdfRestException):
            self.my_ktbs.post_graph(graph)

    def test_post_no_type_to_base(self):
        graph = Graph()
        created = BNode()
        graph.add((self.my_ktbs.uri, RDFS.seeAlso, created))
        graph.add((created, RDF.type, KTBS.hasModel)) # in correct NS
        with assert_raises(RdfRestException):
            self.my_ktbs.post_graph(graph)

    def test_post_bad_source1a(self):
        base1 = self.my_ktbs.create_base()
        base2 = self.my_ktbs.create_base()
        model = base1.create_model()
        trace1 = base1.create_stored_trace(None, model)
        g = Graph()
        with assert_raises(InvalidDataError):
            # forcing untrusted content with parameter Graph
            # so we get an InvalidDataError from engine.base
            trace2 = base2.create_computed_trace(None, KTBS.filter, {},
                                                 [trace1], graph=g)

    def test_post_bad_source1b(self):
        base1 = self.my_ktbs.create_base()
        base2 = self.my_ktbs.create_base()
        model = base1.create_model()
        trace1 = base1.create_stored_trace(None, model)
        with assert_raises(ValueError):
            # content will be trusted, so we get a ValueError from api.ase
            trace2 = base2.create_computed_trace(None, KTBS.filter, {},
                                                 [trace1])

    def test_post_bad_source2a(self):
        # testing with URI in same base
        base = self.my_ktbs.create_base()
        model = base.create_model()
        trace1 = base.create_stored_trace(None, model)
        g = Graph()
        with assert_raises(InvalidDataError):
            # forcing untrusted content with parameter Graph
            # so we get an InvalidDataError from engine.base
            trace2 = base.create_computed_trace(None, KTBS.filter, {},
                                                 [trace1.uri[:-1]], graph=g)

    def test_post_bad_source2a(self):
        # testing with URI in same base
        base = self.my_ktbs.create_base()
        model = base.create_model()
        trace1 = base.create_stored_trace(None, model)
        with assert_raises(ValueError):
            # content will be trusted, so we get a ValueError from api.ase
            trace2 = base.create_computed_trace(None, KTBS.filter, {},
                                                 [trace1.uri[:-1]])
        

    def test_blank_obsels(self):
        base = self.my_ktbs.create_base()
        model = base.create_model()
        otype = model.create_obsel_type(label="MyObsel")
        trace = base.create_stored_trace(None, model)
        obs1 = trace.create_obsel(None, otype, 1000, subject="alice")
        obs2 = trace.create_obsel(None, otype, 1000, subject="alice")
        assert obs1.uri != obs2.uri

    def test_monotonicity(self):
        base = self.my_ktbs.create_base()
        model = base.create_model()
        myot = model.create_obsel_type("#myot")
        myrt = model.create_obsel_type("#myrt")
        trace = base.create_stored_trace(None, model)
        trace.default_subject = "alice"
        trace.pseudomon_range = 100
        obsels = trace.obsel_collection

        tags = [obsels.str_mon_tag, obsels.pse_mon_tag, obsels.log_mon_tag]
        o100 = trace.create_obsel("o100", myot, 100)
        eq_(get_change_monotonicity(trace, tags), 3)
        eq_(last_obsel(trace), o100.uri)
        o200 = trace.create_obsel("o200", myot, 200)
        eq_(get_change_monotonicity(trace, tags), 3)
        eq_(last_obsel(trace), o200.uri)
        o150 = trace.create_obsel("o150", myot, 150)
        eq_(get_change_monotonicity(trace, tags), 2)
        eq_(last_obsel(trace), o200.uri)
        o300 = trace.create_obsel("o300", myot, 300)
        eq_(get_change_monotonicity(trace, tags), 3)
        eq_(last_obsel(trace), o300.uri)
        o350 = trace.create_obsel("o350", myot, 350, relations=[(myrt, o200)])
        eq_(get_change_monotonicity(trace, tags), 1)
        eq_(last_obsel(trace), o350.uri)
        o400 = trace.create_obsel("o400", myot, 400,
                                  inverse_relations=[(o350, myrt)])
        eq_(get_change_monotonicity(trace, tags), 3)
        eq_(last_obsel(trace), o400.uri)
        o450 = trace.create_obsel("o450", myot, 450,
                                  inverse_relations=[(o350, myrt)])
        eq_(get_change_monotonicity(trace, tags), 2)
        eq_(last_obsel(trace), o450.uri)
        o45b = trace.create_obsel("o45b", myot, 450)
        eq_(get_change_monotonicity(trace, tags), 3)
        with obsels.edit() as editable:
            editable.remove((o45b.uri, None, None))
            editable.remove((None, None, o45b.uri))
        eq_(get_change_monotonicity(trace, tags), 0)

        eq_(set([obsels.etag]), set(obsels.iter_etags()))
        eq_(set([obsels.etag]), set(obsels.iter_etags({"maxe": 500})))
        eq_(set([obsels.etag]), set(obsels.iter_etags({"maxe": 450})))
        eq_(set([obsels.etag, obsels.str_mon_tag]),
            set(obsels.iter_etags({"maxe": 400})))
        eq_(set([obsels.etag, obsels.str_mon_tag, obsels.pse_mon_tag]),
            set(obsels.iter_etags({"maxe": 300})))

        trace.pseudomon_range = 200
        eq_(get_change_monotonicity(trace, tags), 0)

    def test_post_multiple_obsels(self):
        base = self.my_ktbs.create_base()
        model = base.create_model()
        otype0 = model.create_obsel_type("#MyObsel0")
        otype1 = model.create_obsel_type("#MyObsel1")
        otype2 = model.create_obsel_type("#MyObsel2")
        otype3 = model.create_obsel_type("#MyObsel3")
        otypeN = model.create_obsel_type("#MyObselN")
        trace = base.create_stored_trace(None, model, "1970-01-01T00:00:00Z",
                                         "alice")
        # purposefully mix obsel order,
        # to check whether batch post is enforcing the monotonic order
        graph = Graph()
        obsN = BNode()
        graph.add((obsN, KTBS.hasTrace, trace.uri))
        graph.add((obsN, RDF.type, otypeN.uri))
        obs1 = BNode()
        graph.add((obs1, KTBS.hasTrace, trace.uri))
        graph.add((obs1, RDF.type, otype1.uri))
        graph.add((obs1, KTBS.hasBegin, Literal(1)))
        graph.add((obs1, RDF.value, Literal("obs1")))
        obs3 = BNode()
        graph.add((obs3, KTBS.hasTrace, trace.uri))
        graph.add((obs3, RDF.type, otype3.uri))
        graph.add((obs3, KTBS.hasBegin, Literal(3)))
        graph.add((obs3, KTBS.hasSubject, Literal("bob")))
        obs2 = BNode()
        graph.add((obs2, KTBS.hasTrace, trace.uri))
        graph.add((obs2, RDF.type, otype2.uri))
        graph.add((obs2, KTBS.hasBegin, Literal(2)))
        graph.add((obs2, KTBS.hasEnd, Literal(3)))
        graph.add((obs2, RDF.value, Literal("obs2")))
        obs0 = BNode()
        graph.add((obs0, KTBS.hasTrace, trace.uri))
        graph.add((obs0, RDF.type, otype0.uri))
        graph.add((obs0, KTBS.hasBegin, Literal(0)))

        old_tag = trace.obsel_collection.str_mon_tag
        created = trace.post_graph(graph)
        new_tag = trace.obsel_collection.str_mon_tag

        eq_(len(created), 5)
        eq_(old_tag, new_tag)

        obs0 = trace.get_obsel(created[0])
        eq_(obs0.begin, 0)
        eq_(obs0.end, 0)
        eq_(obs0.subject, "alice")
        eq_(obs0.obsel_type, otype0)
        
        obs1 = trace.get_obsel(created[1])
        eq_(obs1.begin, 1)
        eq_(obs1.end, 1)
        eq_(obs1.subject, "alice")
        eq_(obs1.obsel_type, otype1)
        eq_(obs1.get_attribute_value(RDF.value), "obs1")

        obs2 = trace.get_obsel(created[2])
        eq_(obs2.begin, 2)
        eq_(obs2.end, 3)
        eq_(obs2.subject, "alice")
        eq_(obs2.obsel_type, otype2)
        eq_(obs2.get_attribute_value(RDF.value), "obs2")

        obs3 = trace.get_obsel(created[3])
        eq_(obs3.begin, 3)
        eq_(obs3.end, 3)
        eq_(obs3.subject, "bob")
        eq_(obs3.obsel_type, otype3)

        obsN = trace.get_obsel(created[4])
        assert obsN.begin > 4 # set to current date, which is *much* higher
        eq_(obsN.end, obsN.begin)
        eq_(obsN.subject, "alice")
        eq_(obsN.obsel_type, otypeN)


    def test_lineage(self):
        b = self.my_ktbs.create_base()
        model = b.create_model()
        b.create_stored_trace("t1/", model, default_subject="alice")
        b.create_computed_trace("t2/", KTBS.filter, {"after":10}, ["t1/"])
        b.create_computed_trace("t3/", KTBS.filter, {"before":20}, ["t2/"])
        FILTER_LOG.info("populating t1")
        t1 = b.get("t1/")
        myot = model.create_obsel_type("#myot")
        t1.create_obsel("o05", myot, 05)
        t1.create_obsel("o10", myot, 10)
        t1.create_obsel("o15", myot, 15)
        t1.create_obsel("o20", myot, 20)
        t1.create_obsel("o25", myot, 25)
        eq_(len(t1.obsels), 5)
        FILTER_LOG.info("getting t3")
        assert b.factory(b.uri + "t2/", _no_spawn=True) is None
        assert b.factory(b.uri + "t3/", _no_spawn=True) is None
        t3 = b.get("t3/")
        eq_(len(t3.obsels), 3)
        FILTER_LOG.info("getting t2")
        t2 = b.get("t2/")
        eq_(len(t2.obsels), 4)


class TestKtbsSynthetic(KtbsTestCase):

    def test_ktbs(self):
        my_ktbs = self.my_ktbs
        with assert_raises(MethodNotAllowedError):
            my_ktbs.delete()
        assert_equal(len(my_ktbs.builtin_methods), 4)
        assert_equal(my_ktbs.bases, [])
        base = my_ktbs.create_base(label="My new base")
        print "--- base:", base
        assert_equal(base.label, "My new base")
        base.label = "My base"
        assert_equal(base.label, "My base")
        assert_equal(my_ktbs.bases, [base])

        assert_equal(base.models, [])
        model1 = base.create_model(id=None, label="My first trace-model")
        print "--- model1:", model1
        assert_equal(model1.label, "My first trace-model")
        assert_equal(base.models, [model1])
        assert_equal(model1.unit, KTBS.millisecond)
        model1.unit = KTBS.second
        assert_equal(model1.unit, KTBS.second)
        model2 = base.create_model("model2")
        assert_equal(model2.uri, URIRef(base.uri + "model2"))
        assert_equal(len(base.models), 2)

        assert_equal(model1.obsel_types, [])
        with assert_raises(InvalidDataError):
            model1.create_obsel_type("OpenChat") # leading '#' is missing
        open_chat = model1.create_obsel_type("#OpenChat")
        print "--- obsel type open_chat:", open_chat
        assert_equal(model1.obsel_types, [open_chat])
        with assert_raises(InvalidDataError):
            model1.create_obsel_type("#OpenChat") # already in use
        with_on_channel = model1.create_obsel_type("#WithOnChannel")
        abstract_msg = model1.create_obsel_type("#AbstractMsg", [with_on_channel])
        send_msg = model1.create_obsel_type("#SendMsg", [abstract_msg.uri])
        recv_msg = model1.create_obsel_type("#RecvMsg", ["#AbstractMsg"])
        close_chat = model1.create_obsel_type("#CloseChat", [with_on_channel])
        assert_equal(len(model1.obsel_types), 6)


        assert_equal(model1.attribute_types, [])
        with assert_raises(InvalidDataError):
            model1.create_attribute_type("channel", open_chat)
            # leading '#' is missing
        channel = model1.create_attribute_type("#channel", open_chat)
        print "--- attribute type channel:", channel
        assert_equal(model1.attribute_types, [channel])
        with assert_raises(InvalidDataError):
            model1.create_attribute_type("#channel", open_chat) # already in use
        msg = model1.create_attribute_type("#msg", "#AbstractMsg")
        with assert_raises(InvalidDataError):
            recv_msg.create_attribute_type("from") # leading '#' is missing
        recv_msg.create_attribute_type("#from")
        with assert_raises(InvalidDataError):
            send_msg.create_attribute_type("#from")
            # already in use in this *model1* (even if on another obsel type)
        assert_equal(len(model1.attribute_types), 3)


        assert_equal(model1.relation_types, [])
        with assert_raises(InvalidDataError):
            model1.create_relation_type("onChannel", with_on_channel, "#OpenChat")
            # leading '#' is missing
        on_channel = model1.create_relation_type("#onChannel", with_on_channel,
                                                "#OpenChat")
        print "--- relation type on_channel:", on_channel
        assert_equal(model1.relation_types, [on_channel])
        with assert_raises(InvalidDataError):
            model1.create_relation_type("#onChannel", open_chat, with_on_channel)
            # already in use in this *model1* (even if on another obsel type)
        with assert_raises(InvalidDataError):
            close_chat.create_relation_type("closes", "#OpenChat", [on_channel])
            # leading '#' is missing
        closes = close_chat.create_relation_type("#closes", "#OpenChat",
                                                 [on_channel])
        with assert_raises(InvalidDataError):
            open_chat.create_relation_type("#closes", with_on_channel,
                                           [on_channel])
            # already in use in this *model1* (even if on another obsel type)
        assert_equal(len(model1.relation_types), 2)


        assert_equal(base.methods, [])
        method1 = base.create_method("method1", KTBS.external,
                                     {"command-line": cmdline,
                                      "model": "http://example.org/model",
                                      "origin": "1970-01-01T00:00:00Z"})
        print "--- method1:", method1
        assert_equal(base.methods, [method1])
        with assert_raises(InvalidDataError):
            base.create_method("method2", model1) # parent is not a method
        with assert_raises(InvalidDataError):
            base.create_method("method2", "method3") # parent doesn't exist
        with assert_raises(InvalidDataError):
            base.create_method("method2", "http://example.org/")
            # parent is neither in same base nor built-in
        method2 = base.create_method(None, method1, {"foo": "FOO"},
                                     label="m2")
        if not isinstance(method2, HttpResource):
            ## the test above fails in TestHttpKtbs, because method2.parent
            ## returns a rdfrest.local.StandaloneResource -- this is a side
            ## effect of having the HTTP server in the same process as the
            ## client
            assert method2.parent is method1
        assert_equal(method2.parent.uri, method1.uri)
        assert_equal(method1.children, [method2])
        assert_equal(method2.parameters_as_dict,
                     {"command-line":cmdline,
                      "model": "http://example.org/model",
                      "origin": "1970-01-01T00:00:00Z",
                      "foo":"FOO"})
        assert_equal(method2.get_parameter("foo"), "FOO")
        assert_equal(method2.get_parameter("command-line"), cmdline) # inherited
        method2.set_parameter("foo", "BAR")
        assert_equal(method2.get_parameter("foo"), "BAR")
        with assert_raises(ValueError):
            method2.set_parameter("command-line", "456789") # cannot set inherited
        assert_equal(len(base.methods), 2)
        assert_equal(method1.used_by, [])
        assert_equal(method2.used_by, [])


        assert_equal(base.traces, [])
        with assert_raises(InvalidDataError):
            trace1 = base.create_stored_trace("trace1", model2)
            # URI must end with '/'
        with assert_raises(ValueError):
            trace1 = base.create_stored_trace("trace1/")
            # stored trace must have a model
        trace1 = base.create_stored_trace(None, model2, label="trace1")
        with assert_raises(InvalidDataError):
            trace1 = base.create_stored_trace(trace1.uri, model2)
            # trace already exists
        print "--- trace1:", trace1
        assert_equal(base.traces, [trace1])
        if not isinstance(trace1, HttpResource):
            ## see similar exception above
            assert trace1.model is model2
        assert_equal(trace1.model_uri, model2.uri)
        trace1.model = str(model1.uri)
        if not isinstance(trace1, HttpResource):
            ## see similar exception above
            assert trace1.model is model1
        assert_equal(trace1.model_uri, model1.uri)
        if isinstance(trace1, StandaloneResource):
            ## only the local implementation of AbstractTrace has a unit prop
            assert_equal(trace1.unit, model1.unit)
        assert_equal(lit2datetime(trace1.origin), None)
        trace1.origin = origin = datetime.now(UTC)
        assert (timedelta(microseconds=-1)
                <= (lit2datetime(trace1.origin) - origin)
                <= timedelta(microseconds=1))
        # above, we do not test for equality, because *sometimes* there is a
        # difference of 1µs (rounding error?)
        assert_equal(trace1.default_subject, None)
        trace1.default_subject = "alice"
        assert_equal(trace1.default_subject, "alice")

        assert_equal(trace1.obsels, [])
        trace1.origin = datetime.now(UTC)
        with assert_raises(ValueError):
            obs1 = trace1.create_obsel(None)
            # obsel must have an obsel type
        obs1 = trace1.create_obsel(None, open_chat.uri)
        print "--- obs1:", obs1
        assert_equal(trace1.obsels, [obs1])
        assert_equal(obs1.obsel_type, open_chat)
        assert obs1.begin <= 2, obs1.begin # approximating the delay to 2s max
        assert_equal(obs1.begin, obs1.end)
        assert_equal(obs1.subject, trace1.default_subject)
        obs2 = trace1.create_obsel(None, open_chat, obs1.end+1, obs1.end+2,
                                   "alice", { msg.uri: "hello world" },
                                   [ (on_channel, obs1) ], [], [obs1], "obs #2")

        assert_equal(len(base.traces), 1)
        with assert_raises(InvalidDataError):
            ctr = base.create_computed_trace("ctr", method1)
            # URI must end with '/'
        with assert_raises(ValueError):
            ctr = base.create_computed_trace("ctr/")
            # computed trace must have a model
        ctr = base.create_computed_trace(None, method1, label="ctr")
        with assert_raises(InvalidDataError):
            ctr = base.create_computed_trace(ctr.uri, method1)
            # trace already exists
        print "--- ctr:", ctr
        assert_equal(len(base.traces), 2)
        if not isinstance(ctr, HttpResource):
            ## see similar exception above
            assert ctr.method is method1
        assert_equal(ctr.method.uri, method1.uri)
        ctr.method = str(method2.uri)
        assert_equal(method2.used_by, [ctr])
        assert_equal({"command-line":cmdline,
                      "model": "http://example.org/model",
                      "origin": "1970-01-01T00:00:00Z",
                      "foo":"BAR"},
                     method2.parameters_as_dict) # inherited
        ctr.set_parameter("baz", "BAZ")
        assert_equal({"command-line":cmdline,
                      "model": "http://example.org/model",
                      "origin": "1970-01-01T00:00:00Z",
                      "foo":"BAR",
                      "baz": "BAZ"},
                     ctr.parameters_as_dict)
        assert_equal(ctr.get_parameter("baz"), "BAZ")
        assert_equal(ctr.get_parameter("foo"), "BAR") # inherited
        assert_equal(ctr.get_parameter("command-line"), cmdline) # doubly inher.
        assert_equal(ctr.source_traces, [])
        print "---", "adding source"
        ctr.add_source_trace(trace1.uri)
        assert_equal(ctr.source_traces, [trace1])
        assert_equal(trace1.transformed_traces, [ctr])
        print "---", "removing source"
        ctr.del_source_trace(trace1.uri)
        assert_equal(ctr.source_traces, [])
        assert_equal(trace1.transformed_traces, [])
        ctr.add_source_trace(trace1.uri)
        # TODO SOON tests with model and origin

        with assert_raises(CanNotProceedError):
            base.remove()
        with assert_raises(CanNotProceedError):
            trace1.remove() # used by crt
        with assert_raises(CanNotProceedError):
            method2.remove() # used by crt
        with assert_raises(CanNotProceedError):
            method1.remove() # used by method2
        # TODO SOON uncomment test below once this is implemented
        #with assert_raises(CanNotProceedError):
        #    method1.remove() # used by method2
        ctr.remove()
        trace1.remove()
        assert_equal(base.traces, [])
        model2.remove()
        model1.remove()
        assert_equal(base.models, [])
        method2.remove()
        method1.remove()
        assert_equal(base.methods, [])
        base.remove()
        my_ktbs.force_state_refresh()
        assert_equal(my_ktbs.bases, [])

        #print "--- OK"; assert 0 # force the prints to appear


class TestHttpKtbsSynthetic(HttpKtbsTestCaseMixin, TestKtbsSynthetic):
    """Reusing TestKtbsSynthetic with an HTTP kTBS"""


def get_change_monotonicity(trace, prevtags):
    """Return the monotonicity of the last change to this trace's obsels.

    * 3: strictly monotonic
    * 2: pseudo-monotonic
    * 1: logically monotonic
    * 0: non-monotonic

    Tags are compared with those in prevtags, which is then updated.
    """
    obsels = trace.obsel_collection
    #print "---", "old", prevtags[0][-9:], prevtags[1][-9:], prevtags[2][-9:]
    #print "---", "new", obsels.str_mon_tag[-9:], obsels.pse_mon_tag[-9:], \ obsels.log_mon_tag[-9:]
    if obsels.str_mon_tag == prevtags[0]:
        ret = 3
    elif obsels.pse_mon_tag == prevtags[1]:
        ret = 2
    elif obsels.log_mon_tag == prevtags[2]:
        ret = 1
    else:
        ret = 0
    prevtags[:] = [obsels.str_mon_tag, obsels.pse_mon_tag, obsels.log_mon_tag]
    return ret
        
def last_obsel(trace):
    obsels = trace.obsel_collection
    values = list(obsels.metadata.objects(obsels.uri, METADATA.last_obsel))
    if values:
        assert len(values) == 1
        ends = list(obsels.state.objects(values[0], KTBS.hasEnd))
        assert len(ends) == 1
        return values[0]
    else:
        return None
