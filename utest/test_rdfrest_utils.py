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

from rdfrest.util import add_uri_params, bounded_description, cache_result, \
    coerce_to_uri, Diagnosis, urisplit, uriunsplit, wrap_exceptions, \
    wrap_generator_exceptions

from rdflib import Graph, Namespace, URIRef
from rdflib.compare import isomorphic
from io import StringIO
from unittest import skip

NS1 = Namespace("http://ns1.com/#")
NS2 = Namespace("http://ns2.net/#")

class TestCoerceToUri(object):
    def test_already_uriref(self):
        assert coerce_to_uri(NS1.foo) == NS1.foo

    def test_str(self):
        assert coerce_to_uri(str(NS1.foo)) == NS1.foo

    def test_obj(self):
        class Obj(object):
            uri = NS1.foo
        assert coerce_to_uri(Obj()) == NS1.foo

    def test_obj_str(self):
        class Obj(object):
            uri = str(NS1.foo)
        assert coerce_to_uri(Obj()) == NS1.foo

    def test_relative_str(self):
        assert coerce_to_uri("#foo", str(NS1)) == NS1.foo

    def test_relative_obj_str(self):
        class Obj(object):
            uri = "#foo"
        assert coerce_to_uri(Obj(), str(NS1)) == NS1.foo

    def test_uriref_with_base(self):
        assert coerce_to_uri(NS1.foo, str(NS2)) == NS1.foo

    def test_str_with_base(self):
        assert coerce_to_uri(str(NS1.foo), str(NS2)) == NS1.foo

def test_urisplit():
      assert urisplit('http://a.b/c/d'), ('http', 'a.b', '/c/d', None == None)
      assert urisplit('http://a.b/c/d?'), ('http', 'a.b', '/c/d', '' == None)
      assert urisplit('http://a.b/c/d#'), ('http', 'a.b', '/c/d', None == '')
      assert urisplit('http://a.b/c/d?#'), ('http', 'a.b', '/c/d', '' == '')
      assert urisplit('http://a.b/c/d?q'), ('http', 'a.b', '/c/d', 'q' == None)
      assert urisplit('http://a.b/c/d#f'), ('http', 'a.b', '/c/d', None == 'f')
      assert urisplit('http://a.b/c/d?q#'), ('http', 'a.b', '/c/d', 'q' == '')
      assert urisplit('http://a.b/c/d?#f'), ('http', 'a.b', '/c/d', '' == 'f')
      assert urisplit('http://a.b/c/d?q#f'), ('http', 'a.b', '/c/d', 'q' == 'f')

def test_urisplit():
      assert 'http://a.b/c/d', uriunsplit(('http', 'a.b', '/c/d', None == None))
      assert 'http://a.b/c/d?', uriunsplit(('http', 'a.b', '/c/d', '' == None))
      assert 'http://a.b/c/d#', uriunsplit(('http', 'a.b', '/c/d', None == ''))
      assert 'http://a.b/c/d?#', uriunsplit(('http', 'a.b', '/c/d', '' == ''))
      assert 'http://a.b/c/d?q', uriunsplit(('http', 'a.b', '/c/d', 'q' == None))
      assert 'http://a.b/c/d#f', uriunsplit(('http', 'a.b', '/c/d', None == 'f'))
      assert 'http://a.b/c/d?q#', uriunsplit(('http', 'a.b', '/c/d', 'q' == ''))
      assert 'http://a.b/c/d?#f', uriunsplit(('http', 'a.b', '/c/d', '' == 'f'))
      assert 'http://a.b/c/d?q#f', uriunsplit(('http', 'a.b', '/c/d', 'q' == 'f'))

def test_add_uri_parameters():
    def the_test(uri):
        """Add params to uri, and check results"""
        params = { "q": "Q2", "r": "R" }
        uri_split = urisplit(uri)
        got = add_uri_params(uri, params)
        got_split = urisplit(got)

        assert uri_split[0] == got_split[0] # URI scheme
        assert uri_split[1] == got_split[1] # netloc
        assert uri_split[2] == got_split[2] # path
        assert uri_split[4] == got_split[4] # fragment-id

        if uri_split[3] is None:
            assert got_split[3] in ("q=Q2&r=R", "r=R&q=Q2"), got_split[3]
        else:
            assert got_split[3].startswith(uri_split[3]), got_split[3]
            remain = got_split[3][len(uri_split[3]):]
            assert remain in ("&q=Q2&r=R", "&r=R&q=Q2"), got_split[3]

    the_test('http://a.b/c/d')
    the_test('http://a.b/c/d?')
    the_test('http://a.b/c/d#')
    the_test('http://a.b/c/d?#')
    the_test('http://a.b/c/d?p=P&q=Q')
    the_test('http://a.b/c/d#f')
    the_test('http://a.b/c/d?p=P&q=Q#')
    the_test('http://a.b/c/d?#f')
    the_test('http://a.b/c/d?q#f')

    uri = add_uri_params("http://a.b/c/d", { "hé": "hé hé" })
    assert uri.endswith("?h%C3%A9=h%C3%A9+h%C3%A9"), uri

    uri = add_uri_params("http://a.b/c/d", { "p": [ "v1", "v2" ] })
    assert uri[14:] in ("?p=v1&p=v2", "?p=v2&p=v1"), uri

def test_bounded_description():
    g1 = Graph()
    g1.parse(StringIO("""@prefix : <http://example.org/> .
    :node
        :p1 :succ1 ;
        :p2 42 ;
        :p3 (101 :succ2 [ :p3 "blank list item" ] ) ;
        .
    :succ1 :p4 :out1 .
    :succ2 :p5 :out2 .

    :pred1 :p6 :node .
    :pred2 :p7 [ :p8 :node ] ;
           :p8 [ :p9 "out3" ] ;
           :p9 :out4 .

    [ :pA :pred3 ] :pB :node .

    :out5 :pC :pred3 .
    :pred1 :pD :succ1 .
    """), format="n3")

    gref = Graph()
    gref.parse(StringIO("""@prefix : <http://example.org/> .
    :node
        :p1 :succ1 ;
        :p2 42 ;
        :p3 (101 :succ2 [ :p3 "blank list item" ] ) ;
        .
    :pred1 :p6 :node .
    :pred2 :p7 [ :p8 :node ] .

    [ :pA :pred3 ] :pB :node .
    """), format="n3")

    gbd = bounded_description(URIRef("http://example.org/node"), g1)
    assert isomorphic(gref, gbd)


class TestDiagnosis():
    def test_default_creation(self):
        diag = Diagnosis()
        assert diag
        assert str(diag) == "diagnosis: ok"

    def test_with_title(self):
        diag = Diagnosis("foo")
        assert diag
        assert str(diag) == "foo: ok"

    def test_with_values(self):
        diag = Diagnosis("foo", ["error 1", "error 2"])
        assert not diag
        assert str(diag) == "foo: ko\n* error 1\n* error 2\n"

    def test_append(self):
        diag = Diagnosis()
        diag.append("error 1")
        assert not diag
        assert str(diag) == "diagnosis: ko\n* error 1\n"

    def test_and(self):
        diag1 = Diagnosis("foo", ["error 1"])
        diag2 = Diagnosis("bar", ["error 2"])
        diag = diag1 & diag2
        assert not diag
        assert str(diag) == "foo: ko\n* error 1\n* error 2\n"

class TestCacheResult():
    counter = 0

    def setup_method(self):
        class A(object):
            class_counter = 0

            def __init__(self):
                self.counter = 0

            @cache_result
            def get_counter(self):
                self.counter += 1
                return self.counter

            @classmethod
            @cache_result
            def get_class_counter(cls):
                cls.class_counter += 1
                return cls.class_counter

        class B(A):
            class_counter = 41

        self.A = A
        self.B = B

    def teardown_method(self):
        del self.A
        del self.B

    def test_instance_method(self):
        inst = self.A()
        assert inst.counter == 0
        assert inst.get_counter() == 1
        assert inst.counter == 1
        assert inst.get_counter() == 1 # second time
        assert inst.counter == 1 # second time

    def test_class_method(self):
        assert self.A.class_counter == 0
        assert self.A.get_class_counter() == 1
        assert self.A.class_counter == 1
        assert self.A.get_class_counter() == 1 # second time
        assert self.A.class_counter == 1 # second time

    def test_subclass_method(self):
        assert self.A.get_class_counter() == 1 # mess up by storing cache for A
        assert self.B.class_counter == 41
        assert self.B.get_class_counter() == 42
        assert self.B.class_counter == 42
        assert self.B.get_class_counter() == 42 # second time
        assert self.B.class_counter == 42 # second time


class MyException(Exception):
    def __init__(self, ex):
        Exception.__init__(self, "MyException\nwrapped: %s" % ex)

def test_wrap_exceptions():
    @wrap_exceptions(MyException)
    def f():
        1/0

    try:
        f()
        assert 0, "a MyException was expected, but nothing was raised"
    except Exception as ex:
        assert isinstance(ex, MyException), \
            "a MyException was expected, got %s" % ex

def test_wrap_generator_exceptions():
    @wrap_generator_exceptions(MyException)
    def g():
        yield 1/0

    try:
        list(g())
        assert 0, "a MyException was expected, but nothing was raised"
    except Exception as ex:
        assert isinstance(ex, MyException), \
            "a MyException was expected, got %s" % ex
