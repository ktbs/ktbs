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

"""I provide a general core factory.

While :meth:`ICore.factory <rdfrest.interface.ICore.factory>` aims at
producing a resource of the *same kind* as the target, it may be necessary, in
some cases, to navigate a link to a resource of another kind:

  * from a local resource to a remote one
  * from a remote resource to a local one
  * from a local resource to a local resource handled by another service
  * from a remote resource to a remote one using a different protocol

For this, this module provides its own :func:`factory` function.

.. autofunction:: factory

But this function needs to know all the implementations of
:class:`.interface.ICore` and all implemented
`services <.local.Service>`:class:. This is what :func:`register_implementation`
and :func:`register_service` are about, respectively.

.. autofunction:: register_implementation

.. autofunction:: register_service

.. autofunction:: unregister_service

Note that this module automatically registers all the implementations shipped
with rdfrest; furthermore, :class:`.local.Service` automatically registers all
its instances. However, you should check before you call :func:`factory` that:

  * all the external implementations have been registered (this is usually done
    by simply importing them, as :meth:`register_implementation` is meant to be
    used as a class decorator);
  * all the services you rely on have been instanciated.

"""
# implementation and services are stored in lexicographic order of the URI
# prefix they handle; by using a bisect search, we find the most specific
# implementation/service for a given URI.

from bisect import bisect, insort

from ..cores import ICore
from ..util import coerce_to_uri


_IMPL_REG_KEYS = []
_IMPL_REGISTRY = {}

def register_implementation(uri_prefix):
    """Registers a subclass of :class:`.interface.ICore`.

    This is to be used as a decorator generator, as in::

        @register_implementation("xtp://")
        class XtpResource(rdfrest.interface.ICore):
            '''Implementation of REST resource over the XTP protocol.'''
            #...

    :param str uri_prefix: the URI prefix that this implementation can handle
    :return: the class decorator

    The decorated class must implement
    :meth:`factory <rdfrest.interface.ICore.factory>` as a class method.b
    """
    uri_prefix = str(uri_prefix)
    def decorator(cls):
        """Decorator created by :func:`register_implementation`"""
        assert issubclass(cls, ICore)
        assert cls.factory.im_self is cls, \
            "%s.factory should be a classmethod" % cls.__name__
        assert uri_prefix not in _IMPL_REGISTRY
        _IMPL_REGISTRY[uri_prefix] = cls.factory
        insort(_IMPL_REG_KEYS, uri_prefix)
        return cls
    return decorator

def register_service(service):
    """Register a `.local.Service`:class:.

    NB: this need normally not be called directly, as
    :meth:`.local.Serice.__init__` already does it.
    """
    assert isinstance(service, rdfrest.cores.local.Service)
    assert service.root_uri not in _IMPL_REGISTRY
    _IMPL_REGISTRY[service.root_uri] = service.get
    insort(_IMPL_REG_KEYS, service.root_uri)

def unregister_service(service):
    """Unregister a `.local.Service`:class:.

    NB: this beed normally not be called directlt, as
    :meth:`.local.Serice.__del__` already does it.
    """
    assert isinstance(service, rdfrest.cores.local.Service)
    if service.root_uri in _IMPL_REGISTRY:
        assert _IMPL_REGISTRY[service.root_uri] == service.get
        del _IMPL_REGISTRY[service.root_uri]

        i = bisect(_IMPL_REG_KEYS, service.root_uri) - 1
        assert _IMPL_REG_KEYS[i] is service.root_uri
        del _IMPL_REG_KEYS[i]
    
def factory(uri, _rdf_type=None, _no_spawn=False):
    """I return a resource of the appropriate class.

    If no appropriate implementation can be found, None is returned.

    :param uri: the URI of the resource to instanciate
    :type  uri: basestring
    :param _rdf_type: a hint at the expected RDF type of the resource
    :type  _rdf_type: :class:`~rdflib.URIRef`
    :param _no_spawn: if True, only *pre-existing* python objects will be
                      returned (may not be honnored by all implementations)
    :type  _no_spawn: bool

    :rtype: :class:`.interface.ICore`

    When using this function, it is a good practice to indicate the expected
    return type, either informally (with a comment) or formally, with a
    statement of the form::
    
        assert isinstance(returned_object, expected_class)
    
    Note that the expected class will usually be an abstract class (a
    `registered <register_wrapper>`:func: mix-in class) rather than a specific
    implementation.
    """
    uri = coerce_to_uri(uri)
    match = ""
    for i in _IMPL_REG_KEYS:
        if uri.startswith(i) and len(i) > len(match):
            match = i
    if match:
        return _IMPL_REGISTRY[match](uri, _rdf_type, _no_spawn)
    else:
        return None
    
# ensure all shipped implementations are registered
import rdfrest.cores.http_client  # unused import #pylint: disable=W0611

# needed by some assertions
import rdfrest.cores.local
