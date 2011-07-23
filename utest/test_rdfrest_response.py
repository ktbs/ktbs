from nose.tools import eq_
from rdfrest.response import *
from webob.etag import ETagMatcher

MATCHER = ETagMatcher.parse('"ab","W/cd",W/"ef",W/"W/gh"')

def test_my_response():
    res = MyResponse(headerlist=[("etag", 'W/"ab"')])
    assert isinstance(res.etag, WeakEtag), repr(res.etag)
    assert str(res.etag) == "ab", repr(str(res.etag))
    assert res.headers.get("etag") == 'W/"ab"'
    res.etag = WeakEtag("cd")
    assert isinstance(res.etag, WeakEtag), repr(res.etag) # after setting
    assert str(res.etag) == "cd", repr(str(res.etag))
    assert res.headers.get("etag") == 'w/"cd"'

def test_repr():
    eq_(repr(WeakEtag('ab')), "WeakEtag(%r)" % 'ab')
    eq_(str (WeakEtag('ab')), 'ab')

def test_strong():
    def check(value, what):
        if what == "parse":
            assert not isinstance(new_parse_etag_response(value), WeakEtag)
        else:
            if value[0] != '"':
                expected = '"%s"' % value
            else:
                expected = value
            eq_(new_serialize_etag_response(new_parse_etag_response(value)),
                expected)
                       
    for i in [ 'ab', '"ab"', '"W/ab"', '"w/ab"' ]:
        yield check, i, "parse"
        yield check, i, "serialize"

def test_weak():
    def check(value, what):
        if what == "parse":
            assert isinstance(new_parse_etag_response(value), WeakEtag)
        else:
            if value[2] != '"':
                expected = 'w/"%s"' % value[2:]
            else:
                expected = 'w/%s' % value[2:]
            eq_(new_serialize_etag_response(new_parse_etag_response(value)),
                expected)

    for i in [ 'W/ab', 'W/"ab"', 'W/"W/ab"', 'W/"w/ab"',
               'w/ab', 'w/"ab"', 'w/"W/ab"', 'w/"w/ab"', ]:
        yield check, i, "parse"
        yield check, i, "serialize"

def test_positive_matches():
    def check(value):
        assert new_parse_etag_response(value) in MATCHER
    for i in [ 'ab', '"ab"', '"W/cd"', 'ef', '"ef"', 'W/ef', 'W/"ef"',
               '"W/gh"', 'W/W/gh', 'W/"W/gh"',
               # also testing weak versions of the strong etags in MATCHER
               'W/ab', 'W/"ab"', 'W/W/cd', 'W/"W/cd"',
               ]:
        yield check, i
    
def test_negative_matches():
    def check(value):
        assert new_parse_etag_response(value) not in MATCHER
    for i in [ 'cd', '"cd"', 'W/cd', 'W/"cd"', '"W/ef"', 'W/gh', 'W/"gh"' ]:
        yield check, i
