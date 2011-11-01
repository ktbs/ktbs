#    This file is part of RDF-REST <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
I provide :class:`Resource`, which defines the *common interface* to all
components of an an RDF-Rest `.service.Service`:class:.

Instances of this class are typically retrieved from a
`~.service.Service`:class:, either by its property
`~.service.Service.root`:attr: property or by its method
`~.service.Service.get`:meth:.

Note that every resource is identified by a URI. Howevever, only URIs without
any query-string (the part of the URI after the '?') or fragment-identifier
(the part of the URI after the '#') are allowed.

.. _query-strings-in-rdfrest:

Note that from the perspective of both REST and RDF, every URI identifies a
different resource, and query-string and fragment-identifiers are no
exception: ``http://a.b/c/d``, ``http://a.b/c/d?e=f`` and ``http://a.b/c/d#e``
are *three* different resources. In practice, however, URIs that differ only
by their query-string and/or fragment-identifier usually identify resources
that are closely related (if not "variants" of the same resource).  RDF-REST
endorses this practice by allowing `parameters` in all REST operations
(:meth:`~Resource.rdf_get`, :meth:`~Resource.rdf_put`,
:meth:`~Resource.rdf_post` and :meth:`~Resource.rdf_delete`). The REST way to
look at it is to consider that an instance of :class:`Resource` is in fact
handling a *family* of related resources.

.. _frag-ids-in-rdfrest:

As for fragment-identifiers, the underlying graph of a resource may contain
URIs with fragment-identifiers in addition to the URI of the resource
itself. Again, those additional resources are not handled independantly by
RDF-REST; however, subclasses of :class:`Resource` may constrain their
appearance and their properties.
"""
from contextlib import contextmanager
from rdflib import Graph, RDF, RDFS, URIRef
from rdflib.compare import graph_diff
from rdflib.graph import ReadOnlyGraphAggregate

from rdfrest.exceptions import InvalidParametersError, InvalidUriError, \
    MethodNotAllowedError
from rdfrest.namespaces import RDFREST
from rdfrest.utils import Diagnosis, make_fresh_uri, urisplit

class Resource(object):
    """
    I provide core functionalities for implementing
    :class:`~rdfrest.service.Service` resources.

    :param service: the service this resource is a part of
    :type  service: rdfrest.service.Service
    :param uri:     the resource URI
                    (`without query-string <query-strings-in-rdfrest>`:ref:)
    :type  uri:     rdflib.URIRef


    .. note:: Subclassing Resource

        This class only provides an implementation for :meth:`rdf_get`. For
        implementing other REST operations, subclasses should first consider
        using the mixin classes provided by :mod:`rdfrest.mixins`.

        For other functionalities, subclasses can access the underlying graph
        with the two following members:

        * `_graph` is a read-only view on this resource's graph,

        * `_edit` provides a python-context (to be used with the ``with``
          statement) returning the underlying mutable graph.
          
        Modifications can only be done through the `_edit` context::

            with self._edit as graph:
                graph.add((self.uri, a_property, a_value))

        **Important**: unlike `rdf_post`, the `_edit` context does *not* do
        any integrity checking (e.g. it does not call
        :meth:`check_new_graph`); it is intended for internal use (in
        subclasses), and assumes that the implementers know what they are
        doing.
    """

    # subclasses must override this attribute; see Service.register
    RDF_MAIN_TYPE = RDFS.Resource # just to please pylint really

    def __init__(self, service, uri):
        assert isinstance(uri, URIRef), repr(uri)

        if urisplit(uri)[3:] != (None, None):
            raise InvalidUriError("URI has query-string and/or "
                                  "fragment-identifier <%s>" % uri)
        self.service = service
        self.uri = uri
        self.__graph = mutable_graph = Graph(service.store, uri)
        self._graph = ReadOnlyGraphAggregate([mutable_graph])
        self._private = Graph(service.store, URIRef(uri+"#private"))
        self._edit_level = 0


    @property
    @contextmanager
    def _edit(self):
        """I implement the _edit context. See `Resource`"""
        with self.service:
            level = self._edit_level
            self._edit_level += 1
            yield self.__graph
            if level == 0:
                self.ack_edit()
            self._edit_level = level

    ## public methods ##

    @classmethod
    def create_root_graph(cls, uri, service):
        """Return a bootstrap graph for a service root.

        :param uri:       the URI of the resource to create
        :type  uri:       rdflib.URIRef
        :param uri:       the service of which we are creating the root
        :type  uri:       rdfrest.service.Service

        :rtype: rdflib.Graph

        This method is used by :class:`~rdfrest.service.Service` on the class
        registered as the root class, in order to populate an empty store. The
        return value will then be passed to :meth:`create`.

        The default behaviour is to return a graph with a single triple,
        stating that this resource has ``rdf:type`` ``RDF_MAIN_TYPE``.
        """
        # unused argument service #pylint: disable=W0613
        ret = Graph()
        ret.add((uri, _RDF_TYPE, cls.RDF_MAIN_TYPE))
        return ret

    def rdf_get(self, parameters=None):
        """Return a read-only graph describing this resource.

        More precisely, the returned graph describes the resource
        identified by the URI `<self.uri>?<parameters>` .

        :param parameters: the query string parameters (see
                           `below <rdfrest-paramaters>`:ref:)
        :type  parameters: dict

        :return: a graph representing the resource, dynamically reflecting
                 the changes in the resource
        :rtype: rdflib.Graph
        :raise: :class:`~rdfrest.exceptions.InvalidParametersError`

        .. _rdfrest-paramaters:

        If not None, `parameters` is expected to be a dict with ASCII strings
        as their keys and either unicode strings or lists of unicode strings
        as their value. Note that the empty dict is semantically different
        from None, as ``http://example.org/?`` is semantically different from
        ``http://example.org/``.

        The default behaviour is to accept no `parameters`.

        .. warning::
            As stated above, the returned graph is dynamic and will reflect the
            changes made to the resource after it has been returned.

            If one wants a static snapshot of the state of the resoutce, one
            has to build it immediately after calling rdf_get.
        """
        # about the warning above:
        # this design decision comes from the fact that it is more efficient
        # to build a ReadOnlyGraphAggregate than to copy every triple of
        # self._graph into another graph.
        if parameters is not None:
            raise InvalidParametersError()
        return self._graph

    def rdf_put(self, new_graph, parameters=None):
        """Update this resource with RDF data.

        :param new_graph:  an RDF graph
        :type  new_graph:  rdflib.Graph
        :param parameters: the query string parameters (see
                           `above <rdfrest-paramaters>`:ref:)
        :type  parameters: dict

        :raise: :class:`~rdfrest.exceptions.RdfRestException`
        """
        # unused argument #pylint: disable=W0613
        raise MethodNotAllowedError("PUT on %s" % self.uri)

    def rdf_post(self, new_graph, parameters=None):
        """
        Post RDF data to this resource.

        :param new_graph:  an RDF graph
        :type  new_graph:  rdflib.Graph
        :param parameters: the query string parameters (see
                           `above <rdfrest-paramaters>`:ref:)
        :type  parameters: dict

        :return: the list of created URIs, possibly empty
        :raise: :class:`~rdfrest.exceptions.RdfRestException`
        """
        # unused argument #pylint: disable=W0613
        raise MethodNotAllowedError("POST on %s" % self.uri)

    def rdf_delete(self, parameters=None):
        """Delete this resource from the corresponding service.

        :param parameters: the query string parameters (see
                           `above <rdfrest-paramaters>`:ref:)
        :type  parameters: dict

        :raise: :class:`~rdfrest.exceptions.RdfRestException`
        """
        # unused argument #pylint: disable=W0613
        raise MethodNotAllowedError("DELETE on %s" % self.uri)


    ## hook methods ##

    @classmethod
    def check_new_graph(cls, uri, new_graph,
                        resource=None, added=None, removed=None):
        """**Hook**: check that a graph is a valid representation of this
        resource class.

        This hook method is called by :meth:`create` and :meth:`rdf_put`;
        calling it directly is usually not required.

        :param uri:       the URI of the resource described by `new_graph`
        :type  uri:       rdflib.URIRef
        :param new_graph: graph to check
        :type  new_graph: rdflib.Graph

        The following parameter will always be set  when `check_new_graph` is
        used to update and *existing* resource; for creating a new resource, it
        will always be `None`.

        :param resource:  the resource to be updated

        The following parameters only make sense when updating an existing
        resource. They are *not* automatically set by `rdf_put`, as they may
        not be used. However, any implementation may set them by using
        `compute_added_and_removed` and should therefore pass them along.

        :param added:     if not None, an RDF graph containg triples to be
                          added
        :param removed:   if not None, an RDF graph containg triples to be
                          removed

        :rtype: a `rdfrest.utils.Diagnosis`:class:

        This class method can be overridden by subclasses that have constraints
        on the representation of their instances.
        
        The default implementation accepts any graph.
        """
        # unused arguments "pylint: disable=W0613
        return Diagnosis("check_new_graph")

    @classmethod
    def mint_uri(cls, target, new_graph, created, suffix=""):
        """**Hook**: Mint a URI for a resource of that class.

        This hook method is called by :class:`rdflib.mixins.WithPostMixin`;
        calling it directly is usually not required.

        :param target:    the resource to which `new_graph` has been posted
        :type  target:    rdfrest.resource.Resource
        :param new_graph: a description of the resource for which to mint a URI
        :type  new_graph: rdflib.Graph
        :param created:   the non-URIRef node representing the resource in
                          $`new_graph`
        :type  created:   rdflib.Node
        :param suffix:    a string that will be added at the end of the URI
        :type  suffix:    str

        :rtype: rdflib.URIRef

        The default behaviour is to generate a child URI of `target`'s uri,
        with a name derived from the class name.
        """
        # unsused argument #pylint: disable=W0613
        target_uri = target.uri
        if target_uri[-1] != "/":
            target_uri += "/"
        prefix = "%s%s-" % (target_uri, cls.__name__.lower())
        return make_fresh_uri(
            target._graph, # access to protected member #pylint: disable=W0212
            prefix,
            suffix,
            )

    def ack_edit(self):
        """**Hook**: performs some post processing after editing this resource.

        This hook method is called when exiting the context `self._edit` (see
        `Resource above`:class:); calling it directly may *corrupt the
        service*.

        Note that it is safe for this method to raise an exception; it will be
        handled as if it had been raised *just before* exiting the context.

        The default implementation does nothing.
        """

    @classmethod
    def store_graph(cls, service, uri, new_graph, resource=None):
        """**Hook**: store data in order to create a new resource in the
        service.

        This hook method is called by :meth:`rdf_put` and :meth:`_create`
        (hence indirectly by :meth:`rdf_post`); calling it directly may
        *corrupt the service*.

        :param service:   the service in which to create the resource
        :type  service:   rdfrest.service.Service
        :param uri:       the URI of the resource to create
        :type  uri:       rdflib.URIRef
        :param new_graph: RDF data describing the resource to create
        :type  new_graph: rdflib.Graph
        :param resource: the resource being updated, if any
        :type  resource: :class:`Resource`

        If `resource` is None, this is a resource creation (though `rdf_post`)
        else, this is an update of that resource (through `rdf_put`).

        Subclasses can overload this method in order to store more metadata;
        they may also *alter* the resource's graph, but they should ensure that
        the altered graph is still acceptable according to
        :meth:`check_new_graph`.

        The default implementation simply store `new_graph` as is in the store,
        and adds a hint to this class in the private graph.
        """
        assert isinstance(uri, URIRef)
        if resource:
            Graph(service.store, uri).remove((None, None, None))
        else:
            private_add = Graph(service.store, URIRef(uri+"#private")).add
            private_add((uri, _HAS_IMPL, cls.RDF_MAIN_TYPE))
            
        graph_add = Graph(service.store, uri).add
        for triple in new_graph:
            graph_add(triple)


def compute_added_and_removed(new_graph, resource, added, removed):
    """I compute the graphs of added triples and of removed triples.

    For  overridden versions of `check_new_graph` that require `added` and
    `removed` to be set, I should be called as::

        added, removed = self._compute_added_and_removed(new_graph,
            resource, added, removed)

    before the call to ``super(...).check_new_graph``.

    NB: if added and removed are not None, I will simply return them, so
    there is no significant overhead.

    NB: if resource is None, this method will return ``(None, None)``, as
    `added` and `removed` do not mean anything.
    """
    if resource is None:
        return None, None
    if added is None:
        assert removed is None
        _, added, removed = graph_diff(
            new_graph,
            resource._graph # _graph is protected #pylint: disable=W0212
            )
    else:
        assert removed is not None

    return added, removed


_HAS_IMPL = RDFREST.hasImplementation
_RDF_TYPE = RDF.type
