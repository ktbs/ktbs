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

from threading import Thread
from wsgiref.simple_server import make_server

from rdflib import BNode, Graph, Literal, RDF, RDFS, URIRef

from datetime import datetime, timedelta
from rdfrest.exceptions import CanNotProceedError, InvalidDataError, \
    InvalidParametersError, MethodNotAllowedError, RdfRestException
from rdfrest.cores.factory import unregister_service
from rdfrest.cores.local import LocalCore
from rdfrest.cores.http_client import HttpClientCore
from rdfrest.http_server import HttpFrontend
from rdfrest.util.iso8601 import UTC
from ktbs.api.ktbs_root import KtbsRootMixin
from ktbs.engine.resource import METADATA
from ktbs.engine.service import KtbsService
from ktbs.methods.filter import LOG as FILTER_LOG
from ktbs.namespace import KTBS
from ktbs.time import lit2datetime
from ktbs.config import get_ktbs_configuration
from ktbs.engine.service import make_ktbs
from .utils import StdoutHandler

# plugin must be loaded for all kTBS tests
import ktbs.plugins.meth_external
ktbs.plugins.meth_external.start_plugin(get_ktbs_configuration())

cmdline = "echo"

class KtbsTestCase(object):

    my_ktbs = None
    service = None

    def setup_method(self):
        ktbs_config = get_ktbs_configuration()
        ktbs_config.set('server', 'port', '12345')
        self.service = KtbsService(ktbs_config)
        self.my_ktbs = self.service.get(self.service.root_uri, [KTBS.KtbsRoot])

    def teardown_method(self):
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

    def setup_method(self):
        super(HttpKtbsTestCaseMixin, self).setup_method()
        ktbs_config = get_ktbs_configuration()
        ktbs_config.set('server', 'send-traceback', 'true')
        ktbs_config.set('logging', 'console-level', 'DEBUG')
        app = HttpFrontend(self.service, ktbs_config)
        #app = HttpFrontend(self.service, cache_control="max-age=60")

        try:
            httpd = make_server("localhost", 12345, app,
                                handler_class=StdoutHandler)
            thread = Thread(target=httpd.serve_forever)
            thread.start()
            self.httpd = httpd
            self.my_ktbs = HttpClientCore.factory("http://localhost:12345/",
                                                  [KTBS.KtbsRoot])
            assert isinstance(self.my_ktbs, KtbsRootMixin)
        except:
            self.teardown_method()
            raise

    def teardown_method(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd = None
        super(HttpKtbsTestCaseMixin, self).teardown_method()


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
        assert get_change_monotonicity(trace, tags) == 3
        assert last_obsel(trace) == o100.uri
        o200 = trace.create_obsel("o200", myot, 200)
        assert get_change_monotonicity(trace, tags) == 3
        assert last_obsel(trace) == o200.uri
        o150 = trace.create_obsel("o150", myot, 150)
        assert get_change_monotonicity(trace, tags) == 2
        assert last_obsel(trace) == o200.uri
        o300 = trace.create_obsel("o300", myot, 300)
        assert get_change_monotonicity(trace, tags) == 3
        assert last_obsel(trace) == o300.uri
        o350 = trace.create_obsel("o350", myot, 350, relations=[(myrt, o200)])
        assert get_change_monotonicity(trace, tags) == 2
        assert last_obsel(trace) == o350.uri
        o375 = trace.create_obsel("o375", myot, 375, relations=[(myrt, o150)])
        assert get_change_monotonicity(trace, tags) == 1
        assert last_obsel(trace) == o375.uri
        o400 = trace.create_obsel("o400", myot, 400,
                                  inverse_relations=[(o375, myrt)])
        assert get_change_monotonicity(trace, tags) == 2
        assert last_obsel(trace) == o400.uri
        o450 = trace.create_obsel("o450", myot, 450,
                                  inverse_relations=[(o350, myrt)])
        assert get_change_monotonicity(trace, tags) == 2
        assert last_obsel(trace) == o450.uri
        o45b = trace.create_obsel("o45b", myot, 450)
        assert get_change_monotonicity(trace, tags) == 3
        with obsels.edit() as editable:
            editable.remove((o45b.uri, None, None))
            editable.remove((None, None, o45b.uri))
        assert get_change_monotonicity(trace, tags) == 0

        assert set([obsels.etag]) == set(obsels.iter_etags())
        assert set([obsels.etag]) == set(obsels.iter_etags({"maxe": 500}))
        assert set([obsels.etag]) == set(obsels.iter_etags({"maxe": 450}))
        assert set([obsels.etag, obsels.str_mon_tag]) == \
            set(obsels.iter_etags({"maxe": 400}))
        assert set([obsels.etag, obsels.str_mon_tag, obsels.pse_mon_tag]) == \
            set(obsels.iter_etags({"maxe": 300}))

        # testing monotonicity on durative obsels
        o1k26 = trace.create_obsel("o1k26", myot, 1200, 1600)
        assert get_change_monotonicity(trace, tags) == 3
        assert last_obsel(trace) == o1k26.uri
        o1k56 = trace.create_obsel("o1k56", myot, 1500, 1600)
        assert get_change_monotonicity(trace, tags) == 3
        assert last_obsel(trace) == o1k56.uri
        o1k46 = trace.create_obsel("o1k46", myot, 1400, 1600)
        assert get_change_monotonicity(trace, tags) == 2
        assert last_obsel(trace) == o1k56.uri
        o1k36 = trace.create_obsel("o1k36", myot, 1300, 1600)
        assert get_change_monotonicity(trace, tags) == 1
        assert last_obsel(trace) == o1k56.uri
        o1k17 = trace.create_obsel("o1k17", myot, 1100, 1700)
        assert get_change_monotonicity(trace, tags) == 3
        assert last_obsel(trace) == o1k17.uri

        trace.pseudomon_range = 200
        assert get_change_monotonicity(trace, tags) == 0

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

        assert len(created) == 5
        assert old_tag == new_tag

        obs0 = trace.get_obsel(created[0])
        assert obs0.begin == 0
        assert obs0.end == 0
        assert obs0.subject == Literal("alice")
        assert obs0.obsel_type == otype0

        obs1 = trace.get_obsel(created[1])
        assert obs1.begin == 1
        assert obs1.end == 1
        assert obs1.subject == Literal("alice")
        assert obs1.obsel_type == otype1
        assert obs1.get_attribute_value(RDF.value) == "obs1"

        obs2 = trace.get_obsel(created[2])
        assert obs2.begin == 2
        assert obs2.end == 3
        assert obs2.subject == Literal("alice")
        assert obs2.obsel_type == otype2
        assert obs2.get_attribute_value(RDF.value) == "obs2"

        obs3 = trace.get_obsel(created[3])
        assert obs3.begin == 3
        assert obs3.end == 3
        assert obs3.subject == Literal("bob")
        assert obs3.obsel_type == otype3

        obsN = trace.get_obsel(created[4])
        assert obsN.begin > 4 # set to current date, which is *much* higher
        assert obsN.end == obsN.begin
        assert obsN.subject == Literal("alice")
        assert obsN.obsel_type == otypeN

    def test_post_multiple_bnode_obsels_w_relations(self):
        base = self.my_ktbs.create_base()
        model = base.create_model()
        otype0 = model.create_obsel_type("#MyObsel0")
        rtype0 = model.create_relation_type("#MyRel0")
        trace = base.create_stored_trace(None, model, "1970-01-01T00:00:00Z",
                                         "alice")
        graph = Graph()
        obs1 = BNode()
        obs2 = BNode()
        obs3 = BNode()
        graph.add((obs1, KTBS.hasTrace, trace.uri))
        graph.add((obs1, RDF.type, otype0.uri))
        graph.add((obs1, KTBS.hasBegin, Literal(1)))
        graph.add((obs1, rtype0.uri, obs2))
        graph.add((obs2, KTBS.hasTrace, trace.uri))
        graph.add((obs2, RDF.type, otype0.uri))
        graph.add((obs2, KTBS.hasBegin, Literal(2)))
        graph.add((obs2, rtype0.uri, obs3))
        graph.add((obs3, KTBS.hasTrace, trace.uri))
        graph.add((obs3, RDF.type, otype0.uri))
        graph.add((obs3, KTBS.hasBegin, Literal(3)))
        graph.add((obs3, rtype0.uri, obs1))

        created = trace.post_graph(graph)

        assert len(created) == 3

        obs1 = trace.get_obsel(created[0])
        obs2 = trace.get_obsel(created[1])
        obs3 = trace.get_obsel(created[2])

        assert obs1.begin == 1
        assert obs2.begin == 2
        assert obs3.begin == 3
        assert obs1.list_related_obsels(rtype0) == [obs2]
        assert obs2.list_related_obsels(rtype0) == [obs3]
        assert obs3.list_related_obsels(rtype0) == [obs1]
        assert obs1.list_relating_obsels(rtype0) == [obs3]
        assert obs2.list_relating_obsels(rtype0) == [obs1]
        assert obs3.list_relating_obsels(rtype0) == [obs2]

    def test_post_no_obsels(self):
        base = self.my_ktbs.create_base()
        model = base.create_model()
        otype0 = model.create_obsel_type("#MyObsel0")
        otype1 = model.create_obsel_type("#MyObsel1")
        otype2 = model.create_obsel_type("#MyObsel2")
        otype3 = model.create_obsel_type("#MyObsel3")
        otypeN = model.create_obsel_type("#MyObselN")
        trace = base.create_stored_trace(None, model, "1970-01-01T00:00:00Z",
                                         "alice")
        graph = Graph()

        old_tag = trace.obsel_collection.str_mon_tag
        with assert_raises(InvalidDataError):
            created = trace.post_graph(graph)
        new_tag = trace.obsel_collection.str_mon_tag
        assert old_tag == new_tag

    def test_post_homonymic_obsels(self):
        """Check that it is impossible to post an obsel with an URI
        that already exists in a trace."""
        base = self.my_ktbs.create_base()
        model = base.create_model()
        otype1 = model.create_obsel_type("#MyObsel1")
        otype2 = model.create_obsel_type("#MyObsel2")
        trace = base.create_stored_trace(None, model, "1970-01-01T00:00:00Z",
                                         "test homonymic obsels")

        obsel = URIRef(trace.uri + 'obs')
        graph1 = Graph()
        graph1.add((obsel, KTBS.hasTrace, trace.uri))
        graph1.add((obsel, RDF.type, otype1.uri))

        graph2 = Graph()
        graph2.add((obsel, KTBS.hasTrace, trace.uri))
        graph2.add((obsel, RDF.type, otype2.uri))

        created = trace.post_graph(graph1)
        with assert_raises(InvalidDataError):
            created_homonymic = trace.post_graph(graph2)

    def test_lineage(self):
        b = self.my_ktbs.create_base()
        model = b.create_model()
        b.create_stored_trace("t1/", model, default_subject="alice")
        b.create_computed_trace("t2/", KTBS.filter, {"after":10}, ["t1/"])
        b.create_computed_trace("t3/", KTBS.filter, {"before":20}, ["t2/"])
        FILTER_LOG.info("populating t1")
        t1 = b.get("t1/")
        myot = model.create_obsel_type("#myot")
        t1.create_obsel("o05", myot, 5)
        t1.create_obsel("o10", myot, 10)
        t1.create_obsel("o15", myot, 15)
        t1.create_obsel("o20", myot, 20)
        t1.create_obsel("o25", myot, 25)
        assert len(t1.obsels) == 5
        FILTER_LOG.info("getting t3")
        # the following asserts rely on the garbage collector,
        # so they fail in some situations and depend on the interpreter
        #assert b.factory(b.uri + "t2/", _no_spawn=True) is None
        #assert b.factory(b.uri + "t3/", _no_spawn=True) is None
        t3 = b.get("t3/")
        assert len(t3.obsels) == 3
        FILTER_LOG.info("getting t2")
        t2 = b.get("t2/")
        assert len(t2.obsels) == 4

    def test_create_subbase(self):
        base1 = self.my_ktbs.create_base()
        new_base_graph = Graph()
        new_base = BNode()
        new_base_graph.add((new_base, RDF.type, KTBS.Base))
        new_base_graph.add((base1.uri, KTBS.contains, new_base))
        uris = base1.post_graph(new_base_graph)
        assert len(uris) == 1
        base2 = base1.factory(uris[0], [KTBS.Base])
        assert (base1.uri, KTBS.contains, base2.uri) in base2.state
        base1.force_state_refresh()
        assert (base1.uri, KTBS.contains, base2.uri) in base1.state

    def test_trace_extension_dt(self):
        k = self.my_ktbs
        b = k.create_base("b/")
        m = b.create_model("m")
        t = b.create_stored_trace("t/", m, origin="1970-01-01T00:00:00Z")
        t.trace_begin_dt = "1970-01-01T00:00:00Z"
        assert t.trace_begin == 0
        t.trace_begin_dt = "1970-01-01T01:00:00Z"
        assert t.trace_begin == 3600000
        t.trace_end_dt = "1970-01-01T02:00:00Z"
        assert t.trace_end == 3600000*2
        t.trace_end_dt = "1970-01-01T03:00:00Z"
        assert t.trace_end == 3600000*3

    def test_origin_now(self, epsilon=0.5):
        k = self.my_ktbs
        b = k.create_base("b/")
        m = b.create_model("m")
        t = b.create_stored_trace("t/", m, origin="now")
        now = datetime.now(UTC)
        delta = t.get_origin(as_datetime=True) - now
        assert abs(delta.total_seconds()) < epsilon

    def test_uri_subject(self):
        bob = URIRef("http://example.org/bob")
        base = self.my_ktbs.create_base()
        model = base.create_model()
        otype0 = model.create_obsel_type("#MyObsel0")
        trace1 = base.create_stored_trace(None, model,
                                         "1970-01-01T00:00:00Z",
                                         bob)
        assert trace1.default_subject == bob
        o1 = trace1.create_obsel("o1", otype0, 1)
        assert o1.subject == bob

        g = Graph()
        o2n = BNode()
        g.add((o2n, KTBS.hasTrace, trace1.uri))
        g.add((o2n, RDF.type, otype0.uri))
        g.add((o2n, KTBS.hasBegin, Literal(2)))
        created = trace1.post_graph(g)
        assert len(created) == 1
        assert trace1.get_obsel(created[0]).subject == bob



class TestObsels(KtbsTestCase):

    my_ktbs = None
    service = None
    epoch = datetime(1970, 1, 1, 0, 0, 0, 0, UTC)

    def setup_method(self):
        super(TestObsels, self).setup_method()
        self.base = b = self.my_ktbs.create_base("b/")
        self.model = m = b.create_model("m")
        self.ot = m.create_obsel_type("#OT1")
        self.at = m.create_obsel_type("#at1")
        self.trace = t = b.create_stored_trace("t/", m,
                                               origin="1970-01-01T00:00:00Z")

    def test_create_no_timestamp(self, epsilon=0.5):
        g = Graph()
        obs = BNode()
        g.add((obs, RDF.type, self.ot.uri))
        g.add((obs, KTBS.hasTrace, self.trace.uri))
        uris = self.trace.post_graph(g)
        now = datetime.now(UTC)
        assert len(uris) == 1
        obs = self.trace.get_obsel(uris[0])
        begin_dt = self.epoch + timedelta(milliseconds=obs.begin)
        delta = now - begin_dt
        assert abs(delta.total_seconds()) < epsilon
        assert obs.end == obs.begin

    def test_create_no_end(self, epsilon=0.5):
        g = Graph()
        obs = BNode()
        g.add((obs, RDF.type, self.ot.uri))
        g.add((obs, KTBS.hasTrace, self.trace.uri))
        g.add((obs, KTBS.hasBegin, Literal(42)))
        uris = self.trace.post_graph(g)
        now = datetime.now(UTC)
        assert len(uris) == 1, uris
        obs = self.trace.get_obsel(uris[0])
        assert obs.begin == 42
        assert obs.end == obs.begin

    def test_create_dt_timestamps(self, epsilon=0.5):
        g = Graph()
        obs = BNode()
        g.add((obs, RDF.type, self.ot.uri))
        g.add((obs, KTBS.hasTrace, self.trace.uri))
        g.add((obs, KTBS.hasBeginDT, Literal(self.epoch.replace(second=1))))
        g.add((obs, KTBS.hasEndDT, Literal(self.epoch.replace(second=2))))
        uris = self.trace.post_graph(g)
        now = datetime.now(UTC)
        assert len(uris) == 1, uris
        obs = self.trace.get_obsel(uris[0])
        assert obs.begin == 1000
        assert obs.end == 2000

    def test_delete_obsel_collection(self):
        t = self.trace
        ot = self.ot
        assert len(t.obsels) == 0
        t.create_obsel(type=ot)
        t.create_obsel(type=ot)
        assert len(t.obsels) == 2
        t.obsel_collection.delete()
        assert len(t.obsels) == 0

    def test_delete_obsel_collection_is_non_monotonic(self):
        t = self.trace
        ot = self.ot
        log_mon_tag = t.obsel_collection.log_mon_tag
        t.create_obsel(type=ot)
        t.create_obsel(type=ot)
        assert log_mon_tag == t.obsel_collection.log_mon_tag
        t.obsel_collection.delete()
        assert log_mon_tag != t.obsel_collection.log_mon_tag

    def test_delete_obsel_collection_with_parameters(self):
        # NB: in the future, this might be allowed
        t = self.trace
        ot = self.ot
        t.create_obsel(type=ot)
        t.create_obsel(type=ot)
        with assert_raises(InvalidParametersError):
            t.obsel_collection.delete({"limit": "1"})

    def test_delete_computed_obsel_collection(self):
        t2 = self.base.create_computed_trace(None, KTBS.filter, {}, [self.trace])
        with assert_raises(MethodNotAllowedError):
            t2.obsel_collection.delete()

    def test_delete_obsel(self):
        t = self.trace
        ot = self.ot
        assert len(t.obsels) == 0
        o1 = t.create_obsel(id="o1", type=ot)
        o2 = t.create_obsel(id="o2", type=ot)
        o3 = t.create_obsel(id="o3", type=ot)
        assert list(t.obsels) == [o1, o2, o3]
        o2.delete()
        assert list(t.obsels) == [o1, o3]

    def test_delete_computed_obsel(self):
        self.trace.create_obsel(id="o1", type=self.ot)
        t2 = self.base.create_computed_trace(None, KTBS.filter, {}, [self.trace])
        assert len(t2.obsels) == 1
        with assert_raises(MethodNotAllowedError):
            t2.obsels[0].delete()

    def test_delete_obsel_is_non_monotonic(self):
        ot = self.ot
        t = self.trace
        log_mon_tag = t.obsel_collection.log_mon_tag
        o1 = t.create_obsel(type=ot)
        o2 = t.create_obsel(type=ot)
        o3 = t.create_obsel(type=ot)
        assert log_mon_tag == t.obsel_collection.log_mon_tag
        o2.delete()
        assert log_mon_tag != t.obsel_collection.log_mon_tag


class TestKtbsSynthetic(KtbsTestCase):

    def test_ktbs(self):
        my_ktbs = self.my_ktbs
        with assert_raises(MethodNotAllowedError):
            my_ktbs.delete()
        assert len(my_ktbs.builtin_methods) == 9
        assert my_ktbs.bases == []
        base = my_ktbs.create_base(label="My new base")
        print("--- base:", base)
        assert base.label == "My new base"
        base.label = "My base"
        assert base.label == "My base"
        assert my_ktbs.bases == [base]

        assert base.models == []
        model1 = base.create_model(id=None, label="My first trace-model")
        print("--- model1:", model1)
        assert model1.label == "My first trace-model"
        assert base.models == [model1]
        assert model1.unit == KTBS.millisecond
        model1.unit = KTBS.second
        assert model1.unit == KTBS.second
        model2 = base.create_model("model2")
        assert model2.uri == URIRef(base.uri + "model2")
        assert len(base.models) == 2

        assert model1.obsel_types == []
        with assert_raises(InvalidDataError):
            model1.create_obsel_type("OpenChat") # leading '#' is missing
        open_chat = model1.create_obsel_type("#OpenChat")
        print("--- obsel type open_chat:", open_chat)
        assert model1.obsel_types == [open_chat]
        with assert_raises(InvalidDataError):
            model1.create_obsel_type("#OpenChat") # already in use
        with_on_channel = model1.create_obsel_type("#WithOnChannel")
        abstract_msg = model1.create_obsel_type("#AbstractMsg", [with_on_channel])
        send_msg = model1.create_obsel_type("#SendMsg", [abstract_msg.uri])
        recv_msg = model1.create_obsel_type("#RecvMsg", ["#AbstractMsg"])
        close_chat = model1.create_obsel_type("#CloseChat", [with_on_channel])
        assert len(model1.obsel_types) == 6


        assert model1.attribute_types == []
        with assert_raises(InvalidDataError):
            model1.create_attribute_type("channel", [open_chat])
            # leading '#' is missing
        channel = model1.create_attribute_type("#channel", [open_chat])
        print("--- attribute type channel:", channel)
        assert model1.attribute_types == [channel]
        with assert_raises(InvalidDataError):
            model1.create_attribute_type("#channel", [open_chat]) # already in use
        msg = model1.create_attribute_type("#msg", ["#AbstractMsg"])
        with assert_raises(InvalidDataError):
            recv_msg.create_attribute_type("from") # leading '#' is missing
        recv_msg.create_attribute_type("#from")
        with assert_raises(InvalidDataError):
            send_msg.create_attribute_type("#from")
            # already in use in this *model1* (even if on another obsel type)
        assert len(model1.attribute_types) == 3


        assert model1.relation_types == []
        with assert_raises(InvalidDataError):
            model1.create_relation_type("onChannel", [with_on_channel], ["#OpenChat"])
            # leading '#' is missing
        on_channel = model1.create_relation_type("#onChannel", [with_on_channel],
                                                ["#OpenChat"])
        print("--- relation type on_channel:", on_channel)
        assert model1.relation_types == [on_channel]
        with assert_raises(InvalidDataError):
            model1.create_relation_type("#onChannel", [open_chat], [with_on_channel])
            # already in use in this *model1* (even if on another obsel type)
        with assert_raises(InvalidDataError):
            close_chat.create_relation_type("closes", ["#OpenChat"], [on_channel])
            # leading '#' is missing
        closes = close_chat.create_relation_type("#closes", ["#OpenChat"],
                                                 [on_channel])
        with assert_raises(InvalidDataError):
            open_chat.create_relation_type("#closes", [with_on_channel],
                                           [on_channel])
            # already in use in this *model1* (even if on another obsel type)
        assert len(model1.relation_types) == 2


        assert base.methods == []
        method1 = base.create_method("method1", KTBS.external,
                                     {"command-line": cmdline,
                                      "model": "http://example.org/model",
                                      "origin": "1970-01-01T00:00:00Z"})
        print("--- method1:", method1)
        assert base.methods == [method1]
        with assert_raises(InvalidDataError):
            base.create_method("method2", model1) # parent is not a method
        with assert_raises(InvalidDataError):
            base.create_method("method2", "method3") # parent doesn't exist
        with assert_raises(InvalidDataError):
            base.create_method("method2", "http://example.org/")
            # parent is neither in same base nor built-in
        method2 = base.create_method(None, method1, {"foo": "FOO"},
                                     label="m2")
        if not isinstance(method2, HttpClientCore):
            ## the test above fails in TestHttpKtbs, because method2.parent
            ## returns a rdfrest.cores.local.LocalCore -- this is a side
            ## effect of having the HTTP server in the same process as the
            ## client
            assert method2.parent is method1
        assert method2.parent.uri == method1.uri
        assert method1.children == [method2]
        assert method2.parameters_as_dict == \
            {"command-line":cmdline,
             "model": "http://example.org/model",
             "origin": "1970-01-01T00:00:00Z",
             "foo":"FOO"}
        assert method2.get_parameter("foo") == "FOO"
        assert method2.get_parameter("command-line") == cmdline # inherited
        method2.set_parameter("foo", "BAR")
        assert method2.get_parameter("foo") == "BAR"
        method2.set_parameter("command-line", "456789") # can override inherited
        method2.set_parameter("command-line", None) # can remove override
        assert len(base.methods) == 2
        assert method1.used_by == []
        assert method2.used_by == []


        assert base.traces == []
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
        print("--- trace1:", trace1)
        assert base.traces == [trace1]
        if not isinstance(trace1, HttpClientCore):
            ## see similar exception above
            assert trace1.model is model2
        assert trace1.model_uri == model2.uri
        trace1.model = str(model1.uri)
        if not isinstance(trace1, HttpClientCore):
            ## see similar exception above
            assert trace1.model is model1
        assert trace1.model_uri == model1.uri
        if isinstance(trace1, LocalCore):
            ## only the local implementation of AbstractTrace has a unit prop
            assert trace1.unit == model1.unit
        assert lit2datetime(trace1.origin) == None
        trace1.origin = origin = datetime.now(UTC)
        assert (timedelta(microseconds=-1)
                <= (lit2datetime(trace1.origin) - origin)
                <= timedelta(microseconds=1))
        # above, we do not test for equality, because *sometimes* there is a
        # difference of 1µs (rounding error?)
        assert trace1.default_subject == None
        trace1.default_subject = URIRef("http://example.org/alice")
        assert trace1.default_subject == URIRef("http://example.org/alice")
        trace1.default_subject = "alice"
        assert trace1.default_subject == Literal("alice")

        assert trace1.obsels == []
        trace1.origin = datetime.now(UTC)
        with assert_raises(ValueError):
            obs1 = trace1.create_obsel(None)
            # obsel must have an obsel type
        obs1 = trace1.create_obsel(None, open_chat.uri)
        print("--- obs1:", obs1)
        assert trace1.obsels == [obs1]
        assert obs1.obsel_type == open_chat
        assert obs1.begin <= 2, obs1.begin # approximating the delay to 2s max
        assert obs1.begin == obs1.end
        assert obs1.subject == trace1.default_subject
        obs2 = trace1.create_obsel(None, open_chat, obs1.end+1, obs1.end+2,
                                   "alice", { msg.uri: "hello world" },
                                   [ (on_channel, obs1) ], [], [obs1], "obs #2")

        assert len(base.traces) == 1
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
        print("--- ctr:", ctr)
        assert len(base.traces) == 2
        if not isinstance(ctr, HttpClientCore):
            ## see similar exception above
            assert ctr.method is method1
        assert ctr.method.uri == method1.uri
        ctr.method = str(method2.uri)
        assert method2.used_by == [ctr]
        assert method2.parameters_as_dict == \
            {"command-line":cmdline, 
             "model": "http://example.org/model",
             "origin": "1970-01-01T00:00:00Z",
             "foo":"BAR"}
            # inherited
        ctr.set_parameter("baz", "BAZ")
        assert ctr.parameters_as_dict == \
            {"command-line":cmdline,
             "model": "http://example.org/model",
             "origin": "1970-01-01T00:00:00Z",
             "foo":"BAR",
             "baz": "BAZ"}
        assert ctr.get_parameter("baz") == "BAZ"
        assert ctr.get_parameter("foo") == "BAR" # inherited
        assert ctr.get_parameter("command-line") == cmdline # doubly inher.
        assert ctr.source_traces == []
        print("---", "adding source")
        ctr.add_source_trace(trace1.uri)
        assert ctr.source_traces == [trace1]
        assert trace1.transformed_traces == [ctr]
        print("---", "removing source")
        ctr.del_source_trace(trace1.uri)
        assert ctr.source_traces == []
        assert trace1.transformed_traces == []
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
        assert base.traces == []
        model2.remove()
        model1.remove()
        assert base.models == []
        method2.remove()
        method1.remove()
        assert base.methods == []
        base.remove()
        my_ktbs.force_state_refresh()
        assert my_ktbs.bases == []

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

class TestMakeKtbs(object):

    my_ktbs = None
    service = None

    def setup_method(self):
        self.my_ktbs = make_ktbs()

    def teardown_method(self):
        if self.my_ktbs is not None:
            unregister_service(self.my_ktbs.service)

    def test_ktbs_default_scheme(self):
        assert self.my_ktbs.uri.startswith('ktbs:')
