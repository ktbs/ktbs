from ktbs.common.utils import extend_api, extend_api_ignore

def test_extend_api():

    @extend_api
    class Foo(object):
        _bar = 0
        def iter_foos(self, desc=False):
            if not desc:
                values = range(5)
            else:
                values = range(0,5,-1)
            for i in values:
                yield i
        def get_bar(self):
            return "BAR %s" % self._bar
        def set_bar(self, val):
            self._bar = val
        def get_baz(self):
            return "BAZ"
        def get_item(self, id):
            return "item %s" % id
        def set_item(self, id, val):
            pass # just to test that no 'item' property is generated
        def iter_items(self, ids):
            pass # just to test that no 'items' property is generated
        @extend_api_ignore
        def get_not_extended(self):
            pass # just to test that no 'not_extended' property is generated
        @extend_api_ignore
        def iter_not_extendeds(self):
            pass # just to test that no 'not_extendeds' property is generated
    
    assert hasattr(Foo, "iter_foos")
    assert hasattr(Foo, "list_foos")
    assert hasattr(Foo, "foos")
    assert hasattr(Foo, "get_bar")
    assert hasattr(Foo, "set_bar")
    assert hasattr(Foo, "bar")
    assert hasattr(Foo, "get_baz")
    assert hasattr(Foo, "baz")
    assert hasattr(Foo, "get_item")
    assert hasattr(Foo, "set_item")
    assert not hasattr(Foo, "item")
    assert hasattr(Foo, "iter_items")
    assert hasattr(Foo, "list_items")
    assert not hasattr(Foo, "items")
    assert not hasattr(Foo, "not_extended")
    assert not hasattr(Foo, "not_extendeds")

    foo = Foo()

    assert list(foo.iter_foos()) == range(5)
    assert list(foo.iter_foos(True)) == range(0,5,-1)
    assert foo.list_foos() == range(5)
    assert foo.list_foos(True) == range(0,5,-1)
    assert foo.foos == range(5)

    assert foo.get_bar() == "BAR 0"
    foo.set_bar(1)
    assert foo.get_bar() == "BAR 1"
    assert foo.bar == "BAR 1"
    foo.bar = 2
    assert foo.bar == "BAR 2"
    assert foo.get_bar() == "BAR 2"

    assert foo.get_baz() == "BAZ"
    assert foo.baz == "BAZ"
    try:
        foo.baz = 42
        assert False, "I was expecting an AttributeError"
    except AttributeError:
        pass

