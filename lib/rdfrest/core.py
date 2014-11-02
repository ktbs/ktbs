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
I define the uniform interface of RDF-REST resources, and a registry of mix-in
classes augmenting it.

Uniform interface
=================

It is defined by class `IResource`:class:.

**Optimisation arguments.** Several of the methods defined in :class:`IResource`
have so called *optimisation arguments*. The caller can provide optimisation
arguments if they think they can help the implementation, by sparing it the work
of either checking data that is known to be correct, or re-computing data that
the caller already has. This puts a high responsibility on the caller, who
should only set those arguments *if they know for certain what they are doing*.
This is why those arguments have a default value and are semi-private (their
name begins with ``'_'``): typically, only subclasses of :class:`IResource`
should use them, and not in all circumstances.

On the other hand, implementations are free to ignore those arguments in
situations when they do not trust the caller (e.g. if it acts on behalf of
another program).

It follows that, when deriving mix-in classes atop the interfaces defined below,
implementors are faced with a delicate choice:

 * either let the implementation do all the checking and computation, which
   might be sub-optimal;
 * or do the checking and computation itself, which breaks the separation of
   concerns (TODO DOC link), and will duplicate work if the implementation
   decides not to trust the client (typically if the implementation is remote).

As a rule of thumb, mix-in implementors should therefore only use optimisation
arguments if they have the information at hand, or if they can quickly compute
it with information at hand. If they have to rely on the implementation (*i.e.*
call methods from the uniform interface), then they should rather let the
implementation do all the work and not use optimisation arguments.

.. autoclass:: IResource
    :members:

Mix-in registry
===============

While REST resource provide a `uniform interface <.interface.IResource>`:class:,
it is often useful to augment this interface with additional methods. In order
to respect the REST philosophy, those methods must not extend the uniform
interface, but merely provide *shortcuts* above it. In other word, they can all
be implemented atop the uniform interface.

In python parlance, this means that those methods can be implemented in a
mix-in class, relying on the `uniform interface <.interface.IResource>`:class:,
but independant on the underlying implementation.

The mix-in registry aims at being a central repository of such mix-in classes;
mix-in classes but be registered with :func:`register_mixin`.
Functions :func:`get_subclass` can then be used to build subclasses of a given
implementation. This is useful to implement :meth:`.interface.IResource.factory`
and :func:`.factory.factory`.

.. autofunction:: register_mixin

.. autofunction:: get_subclass

"""

from types import ClassType

################################################################
#
# Uniform interface for REST resources
#

class IResource(object):
    """
    Abstract interface of an RDF-REST resource.

    .. py:attribute:: uri

        An attribute/property holding the URI of this resource.

    """

    def factory(self, uri, _rdf_type=None, _no_spawn=False):
        """I return an instance for the resource identified by `uri`.

        The returned instance will inherit all the 
        `registered <register_mixin>`:meth: mix-in classes corresponding to the
        ``rdf:type``\s of the resource.

        :param basestring uri: the URI of the resource to instanciate
        :rtype: :class:`IResource`

        Note that this method is only intended to access resources relying on
        the *same implementation* as self (i.e. "neighbour" resources). If this
        is not the case, it may return None even the resource identified by
        `uri` exists but is handled by a different implementation. For the
        latter case, :func:`.factory.factory` should be used instead.

        Optimisation arguments:

        :param _rdf_type: if provided, the expected RDF type of the resource
        :type  _rdf_type: :class:`rdflib.term.URIRef`
        :param _no_spawn: if True, only *pre-existing* python objects will be
                          returned (may not be honnored by all implementations)
        :type  _no_spawn: bool

        When using this function, it is a good practice to indicate the expected
        return type, either informally (with a comment) or formally, with a
        statement of the form::

            assert isinstance(returned_object, expected_class)

        Note that, when describing a mix-in class decorated with
        :func:`register_mixin`, one does not know the exact implementation that
        :meth:`factory` will return, so the expected class will usually be
        another `registered <register_mixin>`:func: mix-in class.

        .. note::

            The interface defines this method as an instance method, so that
            additional method can rely on it to "navigate" from a resource to
            another, without prior knowledge of the destination resource.
            It is nonetheless a good idea, whenever possible, to make it a class
            method, so that the first instance can also be created that way.
        """
        raise NotImplementedError

    def get_state(self, parameters=None):
        """I return the state of this resource as an RDF graph.

        The returned graph will provide a dynamic view of the resource's state:
        as much as possible, it will stay up-to-date when the resource changes.
        It may however get temporarily stale due to cache expiration policy;
        to prevent that, one can use :meth:`force_state_refresh`.

        :param parameters: parameters to alter the meaning of this operation
        :type  parameters: dict-like
        :rtype:            :class:`rdflib.Graph`

        IMPORTANT: the graph returned by :meth:`get_state` is not be used to
        alter the state of the resource (see :meth:`edit` for that); the
        behaviour of the resource if this graph is modified is unspecified.
        """
        raise NotImplementedError

    def force_state_refresh(self, parameters=None):
        """I force a fresh of the graph returned by :meth:`get_state`.

        This method should only be rarely needed, as the graph returned by
        :meth:`get_state` usually updates itself.

        :param parameters: parameters to alter the meaning of this operation
        :type  parameters: dict-like
        """
        raise NotImplementedError

    def edit(self, parameters=None, clear=False, _trust=False):
        """I return a context for modifying the state of this resource.

        Entering this context returns a modifiable graph, containing the state
        of the resource (just has :meth:`get_state`). That graph can be modified
        and the modification will be applied to the resource when exiting the
        context::

            with res.edit() as graph:
                graph.remove(s1, p1, o1)
                graph.add(s2, p2, o2)
            # the modifications apply here to res

        Note that, while inside the edit context, all methods of the resource
        (including :meth:`edit` itself) should not be called, as the internal
        state of the resource is not in sync with the content of the editable
        graph (see exception below).

        :param parameters: parameters to alter the meaning of this operation
        :type  parameters: dict-like
        :param clear:      whether the returned graph should be empty rather
                           than initialized with the current state of this
                           resource
        :type  clear:      bool
                           
        The clear parameter above is mostly used when the new state must be
        parsed from external data rather than modified programatically.

        Optimisation arguments:

        :param _trust: if True, the modification will be immediately applied to
                       this resource's state, without any checking.
        :type  _trust: bool

        It follows that inside a so-called *trusted edit context*, methods of
        the resource can still safely be called, including :meth:`edit` itself.
        Edit context can therefore be embeded, as long as only the inner-most
        context is not trusted.

        NB: it is an error to set both *clear* and *_trust* to True.
        """
        raise NotImplementedError

    def post_graph(self, graph, parameters=None,
                   _trust=False, _created=None, _rdf_type=None):
        """I post an RDF graph to this resource.

        I return the URI of the created resource if any, else None.

        :param parameters: parameters to alter the meaning of this operation
        :type  parameters: dict-like
        :param graph:      the RDF graph to post to this resource
        :type  graph:      :class:`rdflib.Graph`

        :return: the list of created `URIs <rdflib.URIRef>`:class:, possibly
                 empty

        Optimisation arguments:

        :param _trust:    if True, the provided graph is acceptable and requires
                          no modification nor checking.
        :type  _trust:    bool
        :param _created:  the node(s) from `graph` that represent the
                          resource(s) to be created
        :type  _created:  :class:`rdflib.term.Node` or list of them
        :param _rdf_type: the RDF types of the node(s) provided in `_created`
                          (must have the same size)
        :type  _rdf_type: :class:`rdflib.term.URIRef` or list of them
        """
        # Parameter _created can be set with the node from graph that represent
        # the resource to create, which may spare implementation the effort to
        # look for it.
        raise NotImplementedError

    def delete(self, parameters=None, _trust=False):
        """I delete this resource.

        :param parameters:

        :param parameters: a dict-like object containing parameters to alter the
            meaning of this operation

        Optimisation arguments:

        :param _trust: if True, the resource can safely be deleted without any
                       checking.
        :type  _trust:    bool
        """
        raise NotImplementedError


################################################################
#
# Mix-in registry
#

_MIXIN_REGISTRY = {}
_CLASS_CACHE = {} # TODO LATER may be use a WeakValueDict instead?

def register_mixin(rdf_type):
    """I return a decorator to register mix-in classes in the mix-in registry.

    :param rdf_type: the RDF type implemented by the decorated mix-in class
    :type  rdf_type: :class:`rdflib.URIRef`

    No two registered mix-in  classes can implement the same RDF type.

    :see also: :funcet_subclass`
    """
    assert isinstance(rdf_type, basestring), \
        "syntax: @register_mixin(rdf_type) -- you forgot the rdf_type"
    assert rdf_type not in _MIXIN_REGISTRY, \
        "<%s> already registered" % rdf_type
    def register_mixin_decorator(mixin_class):
        """The decorator returned by register_mixin"""
        assert issubclass(mixin_class, IResource)
        _MIXIN_REGISTRY[rdf_type] = mixin_class
        return mixin_class
    return register_mixin_decorator

def get_subclass(cls, rdf_types):
    """I return an appropriate subclass of `cls` for the given `rdf_types`.

    "Appropriate" means that the subclass will inherit the
    `registered mixin <register_mixin>`:func: class associated with
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
            mixin = _MIXIN_REGISTRY.get(typ)
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

