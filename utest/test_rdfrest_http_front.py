from httplib2 import Http
from nose.tools import eq_
from os.path import abspath, dirname, join
from rdflib import Graph, Literal, RDFS, URIRef
from subprocess import Popen, PIPE

URL = "http://localhost:8001/"

class TestHttpFront(object):
    process = None
    server = None

    def setUp(self):
        self.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "test", "rdfrest_demo.py")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        while True:
            line = self.process.stderr.readline()
            if line.startswith("Could not"):
                raise Exception("Could not start server")
            if line.startswith("Starting"):
                break
        self.server = Http()

    def tearDown(self):
        self.process.terminate()

        
    def test_bad_method(self):
        header, content = self.server.request(URL, "XXX")
        eq_(header.status, 405)


    def test_get_not_found(self):
        header, content = self.server.request(URL+"not_there")
        eq_(header.status, 404)

    def test_get(self):
        header, content = self.server.request(URL)
        eq_(header.status, 200)

    def test_get_valid_params(self):
        header, content = self.server.request(URL+"?valid=a")
        eq_(header.status, 200)

    def test_get_invalid_params(self):
        header, content = self.server.request(URL+"?invalid=a")
        eq_(header.status, 404)

    def test_get_redirect(self):
        header, content = self.server.request(URL+"?goto=other", redirections=1)
        assert header.previous is not None
        eq_(header.previous.status, 303)

    def test_get_not_allowed(self):
        header, content = self.server.request(URL+"?notallowed=a")
        eq_(header.status, 405)

    def test_get_proxy(self):
        header, content = self.server.request(URL+"@proxy")
        assert header.previous is not None
        eq_(header.previous.status, 303)


    def test_put_not_found(self):
        header_put, content_put = self.server.request(URL+"not_there", "PUT",
                                                      "")
        eq_(header_put.status, 404)

    def test_put_without_etag(self):
        header_get, content_get = self.server.request(URL)
        reqhead = { "content-type": header_get["content-type"] }
        header_put, content_put = self.server.request(URL, "PUT", content_get,
                                                      reqhead)
        eq_(header_put.status, 403)

    def test_put_bad_content(self):
        header_get, content_get = self.server.request(URL)
        reqhead = {
            "if-match": header_get["etag"],
            "content-type": header_get["content-type"],
            # NB: content-type and etag must be kept consistent
            }
        new_content = ">" # illegal in most syntaxes (Turtle, XML, JSON, HTML)
        header_put, content_put = self.server.request(URL, "PUT", new_content,
                                                      reqhead)
        eq_(header_put.status, 400)

    def test_put_bad_mediatype(self):
        header_get, content_get = self.server.request(URL)
        reqhead = {
            "if-match": header_get["etag"],
            "content-type": "application/x-not-supported"
            }
        new_content = ""
        header_put, content_put = self.server.request(URL, "PUT", new_content,
                                                      reqhead)
        #eq_(header_put.status, 415) # no parser found
        # NB: in fact, the bad mediatype does not match the etag, so we get
        eq_(header_put.status, 412) # pre-condition failed

    def test_put_idem(self, url=URL):
        header_get, content_get = self.server.request(url)
        reqhead = {
            "if-match": header_get["etag"],
            "content-type": header_get["content-type"],
            }
        header_put, content_put = self.server.request(url, "PUT", content_get,
                                                      reqhead)
        eq_(header_put.status, 200)
        assert "etag" in header_put

    def test_put_legal_rdf(self):
        reqhead = { "accept": "text/nt" }
        header_get, content_get = self.server.request(URL, headers=reqhead)
        graph = Graph()
        graph.parse(data=content_get, publicID=URL, format="nt")
        graph.set((URIRef(URL), RDFS.label, Literal("label has been changed")))
        new_content = graph.serialize(format="nt")
        reqhead = {
            "if-match": header_get["etag"],
            "content-type": "text/nt",
            }
        header_put, content_put = self.server.request(URL, "PUT", new_content,
                                                      reqhead)
        eq_(header_put.status, 200)
        assert "etag" in header_put

    def test_put_illegal_rdf(self):
        reqhead = { "accept": "text/nt" }
        header_get, content_get = self.server.request(URL, headers=reqhead)
        graph = Graph()
        graph.parse(data=content_get, publicID=URL, format="nt")
        graph.set((URIRef(URL), URIRef("http://example.org/reserved-ns/"),
                   Literal("ro_out has been changed")))
        new_content = graph.serialize(format="nt")
        reqhead = {
            "if-match": header_get["etag"],
            "content-type": "text/nt",
            }
        header_put, content_put = self.server.request(URL, "PUT", new_content,
                                                      reqhead)
        eq_(header_put.status, 403)

    def test_put_valid_params(self):
        self.test_put_idem(URL+"?valid=a")

    def test_put_invalid_params(self):
        reqhead = { "content-type": "text/turtle" }
        header_put, content_put = self.server.request(URL+"invalid=a", "PUT",
                                                 POSTABLE_TURTLE, reqhead)
        eq_(header_put.status, 404)



    def test_post_not_found(self):
        header_put, content_put = self.server.request(URL+"not_there", "POST",
                                                      "")
        eq_(header_put.status, 404)

    def test_post_bad_content(self):
        new_content = "illegal xml"
        reqhead = { "content-type": "application/rdf+xml" }
        header, content = self.server.request(URL, "POST", new_content, reqhead)
        eq_(header.status, 400)

    def test_post_bad_mediatype(self):
        new_content = ""
        reqhead = { "content-type": "application/x-not-supported" }
        header, content = self.server.request(URL, "POST", new_content, reqhead)
        eq_(header.status, 415)

    def test_post_legal_rdf(self, url=URL):
        #graph = Graph()
        #graph.parse(data=POSTABLE_TURTLE, publicID=url, format="n3")
        #new_content = graph.serialize(format="nt")
        #reqhead = { "content-type": "text/nt" }
        reqhead = { "content-type": "text/turtle" }
        header, content = self.server.request(url, "POST", POSTABLE_TURTLE,
                                              reqhead)
        eq_(header.status, 201)
        assert header["location"]
        header, content = self.server.request(header["location"])
        eq_(header.status, 200)

    def test_post_illegal_rdf(self):
        graph = Graph()
        graph.parse(data=POSTABLE_TURTLE, publicID=URL, format="n3")
        created = next(graph.triples((URIRef(URL), None, None)))[2]
        graph.remove((created, URIRef("http://example.org/other-ns/c1_out"),
                      None))
        new_content = graph.serialize(format="nt")
        reqhead = { "content-type": "text/nt" }
        header, content = self.server.request(URL, "POST", new_content, reqhead)
        eq_(header.status, 403)

    def test_post_valid_params(self):
        self.test_post_legal_rdf(URL+"?valid=a")

    def test_post_invalid_params(self):
        reqhead = { "content-type": "text/turtle" }
        header, content = self.server.request(URL+"?invalid=a", "POST",
                                         POSTABLE_TURTLE, reqhead)
        eq_(header.status, 404)


    def test_delete_not_found(self):
        header_put, content_put = self.server.request(URL+"not_there", "DELETE")
        eq_(header_put.status, 404)

    def test_delete(self):
        reqhead = { "content-type": "text/turtle" }
        header, _       = self.server.request(URL, "POST", POSTABLE_TURTLE,
                                              reqhead)
        url2 = header["location"]
        header, content = self.server.request(url2, "DELETE")
        eq_(header.status, 204)

    def test_delete_conflict(self):
        reqhead = { "content-type": "text/turtle" }
        header, _       = self.server.request(URL, "POST", POSTABLE_TURTLE,
                                              reqhead)
        url2 = header["location"]
        _               = self.server.request(url2, "POST", POSTABLE_TURTLE,
                                              reqhead)
        header, content = self.server.request(url2, "DELETE")
        eq_(header.status, 409)

    def test_delete_valid_params(self):
        reqhead = { "content-type": "text/turtle" }
        header, _       = self.server.request(URL, "POST", POSTABLE_TURTLE,
                                              reqhead)
        url2 = header["location"]
        header, content = self.server.request(url2+"?valid=a", "DELETE")
        eq_(header.status, 204)

    def test_delete_invalid_params(self):
        reqhead = { "content-type": "text/turtle" }
        header, _       = self.server.request(URL, "POST", POSTABLE_TURTLE,
                                              reqhead)
        url2 = header["location"]
        header, content = self.server.request(url2+"?invalid=a", "DELETE")
        eq_(header.status, 404)


    def test_cache_control(self):
        header, _ = self.server.request(URL)
        assert "cache-control" not in header, header["cache-control"]
        reqhead = { "content-type": "text/turtle" }
        header, _ = self.server.request(URL, "POST", POSTABLE_TURTLE, reqhead)
        url2 = header["location"]
        header, _ = self.server.request(url2)
        assert "cache-control" in header


    def test_serialize_error(self):
        # we use the fact that rdfrest_demo can "simulate" a serialize error
        header, content = self.server.request(URL+"?serialize_error=yes")
        eq_(header.status, 550)


    def test_ctype(self):

        for ctype in [ "text/turtle",
                       "application/rdf+xml",
                       "text/nt",
                       ]:
            yield self._do_test_ctype, ctype

    def _do_test_ctype(self, ctype):
        reqhead = { "accept": ctype }
        header_get, content_get = self.server.request(URL, headers=reqhead)
        eq_(header_get.status, 200)
        eq_(header_get["content-type"], ctype)
        reqhead = {
            "if-match": header_get["etag"],
            "content-type": ctype,
            }
        header_put, content_put = self.server.request(URL, "PUT", content_get,
                                                      reqhead)
        eq_(header_put.status, 200)
    


POSTABLE_TURTLE = """
    @prefix : <http://example.org/reserved-ns/> .
    @prefix o: <http://example.org/other-ns/> .

    _:create a :Folder;
        o:c1_out o:foo;
        o:c1n_out o:bar;
        o:c23_out o:bar,
            o:foo;
        :ro_out o:bar;
        :rw_out o:bar .

    <> o:c1_in _:create;
        o:c23_in _:create .

    o:bar o:c1n_in _:create;
        o:c23_in _:create;
        :ro_in _:create;
        :rw_in _:create .
"""

