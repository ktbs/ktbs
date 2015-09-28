#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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

"""
I define a registry of wrapper classes augmenting it cores.

While REST resource provide a `uniform interface <.cores.ICore>`:class:,
it is often useful to augment this interface with additional methods. In order
to respect the REST philosophy, those methods must not extend the uniform
interface, but merely provide *shortcuts* above it. In other word, they can all
be implemented by **wrapping** the uniform interface.

In this implementation, wrappers are implemented as *mix-in* classes relying
of `.cores.ICore`:class:, *e.g.*:

* a class inheriting `.cores.ICore`:class: (or another wrapper),
* defining no ``__init__`` method or internal state,
* with its methods using the methods defined in `.cores.ICore`:class:.

Such classes can then be "mixed in" any class implementing the core interface,
and augment their behaviour independantly of their underlying implementation.

The wrapper registry aims at being a central repository of such mix-in classes;
wrappers but be registered with :func:`register_wrapper`.
Functions :func:`get_wrapped` can then be used to build subclasses of a given
core implementation. This is useful to implement :meth:`.cores.ICore.factory`
and :func:`.cores.factory.factory`.

.. autofunction:: register_wrapper

.. autofunction:: get_wrapped

"""
from types import ClassType
from rdfrest.cores import ICore

_WRAPPER_REGISTRY = {}
_CLASS_CACHE = {} # TODO LATER may be use a WeakValueDict instead?

def get_wrapped(cls, rdf_types):
    """I return an appropriate subclass of `cls` for the given `rdf_types`.

    "Appropriate" means that the subclass will inherit the
    `registered mixin <register_wrapper>`:func: class associated with
    `rdf_types`.

    When inheriting several classes, the rdf types will first be sorted in
    lexicographic order; this ensures for deterministic behaviour when several
    mix-in classes define the same method.
    """
    rdf_types = tuple(sorted(rdf_types))
    ret = _CLASS_CACHE.get((cls, rdf_types))
    if ret is None:
        parents = [cls]
        cls_name = cls.__name__
        for typ in rdf_types:
            mixin = _WRAPPER_REGISTRY.get(typ)
            if mixin is None:
                continue
            else:
                parents.append(mixin)
                cls_name = "%s_%s" % (cls_name, mixin.__name__)
        if len(parents) == 1:
            ret = cls
        else:
            ret = ClassType(cls_name, tuple(parents), {})
        _CLASS_CACHE[(cls, rdf_types)] = ret
    return ret


def register_wrapper(rdf_type):
    """I return a decorator to register mix-in classes in the mix-in registry.

    :param rdf_type: the RDF type implemented by the decorated mix-in class
    :type  rdf_type: :class:`rdflib.URIRef`

    No two registered mix-in  classes can implement the same RDF type.

    :see also: :funcet_subclass`
    """
    assert isinstance(rdf_type, basestring), \
        "syntax: @register_wrapper(rdf_type) -- you forgot the rdf_type"
    assert rdf_type not in _WRAPPER_REGISTRY, \
        "<%s> already registered" % rdf_type
    def register_wrapper_decorator(mixin_class):
        """The decorator returned by register_wrapper"""
        assert issubclass(mixin_class, ICore)
        _WRAPPER_REGISTRY[rdf_type] = mixin_class
        return mixin_class
    return register_wrapper_decorator