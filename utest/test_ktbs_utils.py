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

from ktbs.utils import extend_api, extend_api_ignore
from ktbs.namespace import KTBS

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
