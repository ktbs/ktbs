from rdfrest.utils import coerce_to_uri

from nose.tools import eq_
from rdflib import Namespace

NS1 = Namespace("http://ns1.com/#")
NS2 = Namespace("http://ns2.net/#")


class TestCoerceToUri(object):
    def test_already_uriref(self):
        eq_(coerce_to_uri(NS1.foo), NS1.foo)

    def test_str(self):
        eq_(coerce_to_uri(str(NS1.foo)), NS1.foo)

    def test_obj(self):
        class Obj(object):
            uri = NS1.foo
        eq_(coerce_to_uri(Obj()), NS1.foo)

    def test_obj_str(self):
        class Obj(object):
            uri = str(NS1.foo)
        eq_(coerce_to_uri(Obj()), NS1.foo)

    def test_relative_str(self):
        eq_(coerce_to_uri("#foo", str(NS1)), NS1.foo)

    def test_relative_obj_str(self):
        class Obj(object):
            uri = "#foo"
        eq_(coerce_to_uri(Obj(), str(NS1)), NS1.foo)

    def test_uriref_with_base(self):
        eq_(coerce_to_uri(NS1.foo, str(NS2)), NS1.foo)

    def test_str_with_base(self):
        eq_(coerce_to_uri(str(NS1.foo), str(NS2)), NS1.foo)
