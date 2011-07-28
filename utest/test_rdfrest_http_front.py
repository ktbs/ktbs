from httplib2 import Http
from nose.tools import eq_
from os.path import abspath, dirname, join
from rdflib import Graph, Literal, RDFS, URIRef
from subprocess import Popen, PIPE

PROCESS = None
URL = "http://localhost:8001/"
SERVER = None

def setUp():
    global PROCESS, SERVER
    PROCESS = Popen([join(dirname(dirname(abspath(__file__))),
                          "test", "rdfrest_demo.py")], stderr=PIPE)
    # then wait for the server to actually start:
    # we know that it will write on its stderr when ready
    PROCESS.stderr.read(1)
    SERVER = Http()

def tearDown():
    PROCESS.terminate()


    
def test_bad_method():
    header, content = SERVER.request(URL, "XXX")
    eq_(header.status, 405)


def test_get_not_found():
    header, content = SERVER.request(URL+"not_there")
    eq_(header.status, 404)

def test_get():
    header, content = SERVER.request(URL)
    eq_(header.status, 200)

def test_get_valid_params():
    header, content = SERVER.request(URL+"?valid=a")
    eq_(header.status, 200)

def test_get_invalid_params():
    header, content = SERVER.request(URL+"?invalid=a")
    eq_(header.status, 404)

def test_get_redirect():
    header, content = SERVER.request(URL+"?goto=other", redirections=1)
    assert header.previous is not None
    eq_(header.previous.status, 303)

def test_get_not_allowed():
    header, content = SERVER.request(URL+"?notallowed=a")
    eq_(header.status, 405)



def test_put_not_found():
    header_put, content_put = SERVER.request(URL+"not_there", "PUT", "")
    eq_(header_put.status, 404)

def test_put_without_etag():
    header_get, content_get = SERVER.request(URL)
    reqhead = { "content-type": header_get["content-type"] }
    header_put, content_put = SERVER.request(URL, "PUT", content_get, reqhead)
    eq_(header_put.status, 403)

def test_put_bad_content():
    header_get, content_get = SERVER.request(URL)
    reqhead = {
        "if-match": header_get["etag"],
        "content-type": "application/rdf+xml"
        }
    new_content = "illegal xml"
    header_put, content_put = SERVER.request(URL, "PUT", new_content, reqhead)
    eq_(header_put.status, 400)

def test_put_bad_mediatype():
    header_get, content_get = SERVER.request(URL)
    reqhead = {
        "if-match": header_get["etag"],
        "content-type": "application/x-not-supported"
        }
    new_content = ""
    header_put, content_put = SERVER.request(URL, "PUT", new_content, reqhead)
    eq_(header_put.status, 415)

def test_put_idem(url=URL):
    header_get, content_get = SERVER.request(url)
    print "===", url, header_get.status, content_get
    reqhead = {
        "if-match": header_get["etag"],
        "content-type": header_get["content-type"],
        }
    header_put, content_put = SERVER.request(url, "PUT", content_get, reqhead)
    eq_(header_put.status, 200)
    assert "etag" in header_put

def test_put_legal_rdf():
    reqhead = { "accept": "text/nt" }
    header_get, content_get = SERVER.request(URL, headers=reqhead)
    graph = Graph()
    graph.parse(data=content_get, publicID=URL, format="nt")
    graph.set((URIRef(URL), RDFS.label, Literal("label has been changed")))
    new_content = graph.serialize(format="nt")
    reqhead = {
        "if-match": header_get["etag"],
        "content-type": "text/nt",
        }
    header_put, content_put = SERVER.request(URL, "PUT", new_content, reqhead)
    eq_(header_put.status, 200)
    assert "etag" in header_put

def test_put_illegal_rdf():
    reqhead = { "accept": "text/nt" }
    header_get, content_get = SERVER.request(URL, headers=reqhead)
    graph = Graph()
    graph.parse(data=content_get, publicID=URL, format="nt")
    graph.set((URIRef(URL), URIRef("http://example.org/reserved-ns/"),
               Literal("ro_out has been changed")))
    new_content = graph.serialize(format="nt")
    reqhead = {
        "if-match": header_get["etag"],
        "content-type": "text/nt",
        }
    header_put, content_put = SERVER.request(URL, "PUT", new_content, reqhead)
    eq_(header_put.status, 403)

def test_put_valid_params():
    test_put_idem(URL+"?valid=a")

def test_put_invalid_params():
    reqhead = { "content-type": "text/turtle" }
    header_put, content_put = SERVER.request(URL+"invalid=a", "PUT",
                                             POSTABLE_TURTLE, reqhead)
    eq_(header_put.status, 404)



def test_post_not_found():
    header_put, content_put = SERVER.request(URL+"not_there", "POST", "")
    eq_(header_put.status, 404)

def test_post_bad_content():
    new_content = "illegal xml"
    reqhead = { "content-type": "application/rdf+xml" }
    header, content = SERVER.request(URL, "POST", new_content, reqhead)
    eq_(header.status, 400)

def test_post_bad_mediatype():
    new_content = ""
    reqhead = { "content-type": "application/x-not-supported" }
    header, content = SERVER.request(URL, "POST", new_content, reqhead)
    eq_(header.status, 415)

def test_post_legal_rdf(url=URL):
    #graph = Graph()
    #graph.parse(data=POSTABLE_TURTLE, publicID=url, format="n3")
    #new_content = graph.serialize(format="nt")
    #reqhead = { "content-type": "text/nt" }
    reqhead = { "content-type": "text/turtle" }
    header, content = SERVER.request(url, "POST", POSTABLE_TURTLE, reqhead)
    eq_(header.status, 201)
    assert header["location"]
    header, content = SERVER.request(header["location"])
    eq_(header.status, 200)

def test_post_illegal_rdf():
    graph = Graph()
    graph.parse(data=POSTABLE_TURTLE, publicID=URL, format="n3")
    created = next(graph.triples((URIRef(URL), None, None)))[2]
    graph.remove((created, URIRef("http://example.org/other-ns/c1_out"), None))
    new_content = graph.serialize(format="nt")
    reqhead = { "content-type": "text/nt" }
    header, content = SERVER.request(URL, "POST", new_content, reqhead)
    eq_(header.status, 403)

def test_post_valid_params():
    test_post_legal_rdf(URL+"?valid=a")

def test_post_invalid_params():
    reqhead = { "content-type": "text/turtle" }
    header, content = SERVER.request(URL+"?invalid=a", "POST",
                                     POSTABLE_TURTLE, reqhead)
    eq_(header.status, 404)


def test_delete_not_found():
    header_put, content_put = SERVER.request(URL+"not_there", "DELETE")
    eq_(header_put.status, 404)

def test_delete():
    reqhead = { "content-type": "text/turtle" }
    header, _       = SERVER.request(URL, "POST", POSTABLE_TURTLE, reqhead)
    url2 = header["location"]
    header, content = SERVER.request(url2, "DELETE")
    eq_(header.status, 204)

def test_delete_conflict():
    reqhead = { "content-type": "text/turtle" }
    header, _       = SERVER.request(URL, "POST", POSTABLE_TURTLE, reqhead)
    url2 = header["location"]
    _               = SERVER.request(url2, "POST", POSTABLE_TURTLE, reqhead)
    header, content = SERVER.request(url2, "DELETE")
    eq_(header.status, 409)

def test_delete_valid_params():
    reqhead = { "content-type": "text/turtle" }
    header, _       = SERVER.request(URL, "POST", POSTABLE_TURTLE, reqhead)
    url2 = header["location"]
    header, content = SERVER.request(url2+"?valid=a", "DELETE")
    eq_(header.status, 204)

def test_delete_invalid_params():
    reqhead = { "content-type": "text/turtle" }
    header, _       = SERVER.request(URL, "POST", POSTABLE_TURTLE, reqhead)
    url2 = header["location"]
    header, content = SERVER.request(url2+"?invalid=a", "DELETE")
    eq_(header.status, 404)
    


# TODO
#
# * test a 200 on a GET with parameters (implies that rdfrest_demo.py
#   implements it)
#
# * test a 409 error (implies that rdfrest_demo.py raise CanNotProceedError
#   in some situtation, e.g. when deleting a non-empty folder)
#
# * test a 550 error (implies that we are able to make a serializer fail in
#  rdfrest_demo.py)
#
# * test a working DELETE (implies that rdfrest_demo.py implements it)


def test_ctype():
    for ctype in [ "text/turtle",
                   "application/rdf+xml",
                   "text/nt",
                   ]:
        yield do_text_ctype, ctype

def do_text_ctype(ctype):
    reqhead = { "accept": ctype }
    header_get, content_get = SERVER.request(URL, headers=reqhead)
    eq_(header_get.status, 200)
    eq_(header_get["content-type"], ctype)
    reqhead = {
        "if-match": header_get["etag"],
        "content-type": ctype,
        }
    header_put, content_put = SERVER.request(URL, "PUT", content_get, reqhead)
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

print POSTABLE_TURTLE

