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
I provide :class:`Resource`, the atomic component of an RDF-Rest service.

.. _query-strings-in-rdfrest:

.. note:: Query-strings in RDF-REST

  Note that in strict REST, every URI identifies a different
  resource. Query-strings (the part of the URI after the '?') are not an
  exception: ``http://a.b/c/d`` and ``http://a.b/c/d?e=f`` are two different
  resources. In practice however, URIs that differ only by their query-string
  usually identify resources that are closely related (if not "variants" of
  the same resource).  RDF-REST endorses this practice by requiring that the
  `uri` passed to :class:`Resource` is stripped from the query-string; the
  query-string has to be parsed and passed as `parameters` to the methods
  :meth:`~Resource.rdf_get`, :meth:`~Resource.rdf_put`,
  :meth:`~Resource.rdf_post` and :meth:`~Resource.rdf_delete`.

  Hence, an instance of :class:`Resource` handling parameters is really
  managing a family or related resources.

"""
from contextlib import contextmanager
from rdflib import Graph, RDF, RDFS, URIRef
from rdflib.graph import ReadOnlyGraphAggregate

from rdfrest.exceptions import InvalidDataError, InvalidParametersError, \
    MethodNotAllowedError
from rdfrest.namespaces import RDFREST
from rdfrest.utils import make_fresh_resource

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
    def create(cls, service, uri, new_graph):
        """Create a new resource in the service.

        While ``__init__`` assumes that the `service` already contains the
        resource and only provides a python instance representing it, this
        method assumes that the resource does not exists yet, and does whatever
        is needed to create it.

        :param service:   the service in which to create the resource
        :type  service:   rdfrest.service.Service
        :param uri:       the URI of the resource to create
        :type  uri:       rdflib.URIRef
        :param new_graph: RDF data describing the resource to create
        :type  new_graph: rdflib.Graph

        :return: an instance of `cls`
        :raise: :class:`InvalidDataError` if `new_graph` is not acceptable

        This method should *not* be overridden; instead, subclasses may
        overload :meth:`check_new_graph` and :meth:`store_new_graph` on which
        this method relies.
        """
        errors = cls.check_new_graph(uri, new_graph)
        if errors is not None:
            raise InvalidDataError(errors)
        cls.store_new_graph(service, uri, new_graph)
        return cls(service, uri)

    @classmethod
    def create_root_graph(cls, uri):
        """Return a bootstrap graph for a service root.

        :param uri:       the URI of the resource to create
        :type  uri:       rdflib.URIRef

        :rtype: rdflib.Graph

        This method is used by :class:`~rdfrest.service.Service` on the class
        registered as the root class, in order to populate an empty store. The
        return value will then be passed to :meth:`create`.

        The default behaviour is to return a graph with a single triple,
        stating that this resource has ``rdf:type`` ``RDF_MAIN_TYPE``.
        """
        ret = Graph()
        ret.add((uri, _RDF_TYPE, cls.RDF_MAIN_TYPE))
        return ret

    def rdf_get(self, parameters=None):
        """Return a read-only graph describing this resource.

        More precisely, the returned graph describes the resource
        identified by the URI `<self.uri>?<parameters>` .

        :param parameters: the query string parameters
        :type  parameters: dict

        :return: a graph representing the resource, dynamically reflecting
                 the changes in the resource
        :rtype: rdflib.Graph
        :raise: :class:`~rdfrest.exceptions.InvalidParametersError`


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

        if not parameters:
            return self._graph
        else:
            raise InvalidParametersError()

    def rdf_put(self, new_graph, parameters=None):
        """Update this resource with RDF data.

        :param new_graph:  an RDF graph
        :type  new_graph:  rdflib.Graph
        :param parameters: the query string parameters
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
        :param parameters: the query string parameters
        :type  parameters: dict

        :return: the list of created URIs, possibly empty
        :raise: :class:`~rdfrest.exceptions.RdfRestException`
        """
        # unused argument #pylint: disable=W0613
        raise MethodNotAllowedError("POST on %s" % self.uri)

    def rdf_delete(self, parameters=None):
        """Delete this resource from the corresponding service.

        :param parameters: the query string parameters
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

        The following parameters are used when `check_new_graph` is used to
        update and *existing* resource; for creating a new resource, they will
        always be `None`.

        :param resource:  the resource to be updated
        :param added:     if not None, an RDF graph containg triples to be
                          added
        :param removed:   if not None, an RDF graph containg triples to be
                          removed

        :return: `None` on success, else an error message

        This class method can be overridden by subclasses that have constraints
        on the representation of their instances.
        
        The default implementation accepts any graph.
        """

    @classmethod
    def mint_uri(cls, target, new_graph, created):
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

        :rtype: rdflib.URIRef

        The default behaviour is to generate a child URI of `target`'s uri,
        with a name derived from the class name.
        """
        # unsused argument #pylint: disable=W0613
        target_uri = target.uri
        if target_uri[-1] != "/":
            target_uri += "/"
        prefix = "%s%s-" % (target_uri, cls.__name__.lower())
        return make_fresh_resource(
            target._graph, # access to protected member #pylint: disable=W0212
            prefix,
            )

    def ack_edit(self):
        """**Hook**: performs some post processing editing this resource.

        This hook method is called when exiting the context `self._edit` (see
        `Resource above`:class:); calling it directly may *corrupt the
        service*.

        Note that it is safe for this method to raise an exception; it will be
        handled as if it had been raised *just before* exiting the context.

        The default implementation does nothing.
        """

    @classmethod
    def store_new_graph(cls, service, uri, new_graph):
        """**Hook**: store data in order to create a new resource in the
        service.

        This hook method is called by :meth:`create` and :meth:`rdf_put`;
        calling it directly may *corrupt the service*.

        :param service:   the service in which to create the resource
        :type  service:   rdfrest.service.Service
        :param uri:       the URI of the resource to create
        :type  uri:       rdflib.URIRef
        :param new_graph: RDF data describing the resource to create
        :type  new_graph: rdflib.Graph

        Subclasses can overload this method in order to store more metadata;
        they may also *alter* the resource's graph, but they should ensure that
        the altered graph is still acceptable according to
        :meth:`check_new_graph`.

        The default implementation simply store `new_graph` as is in the store,
        and adds a hint to this class in the private graph.
        """
        assert isinstance(uri, URIRef)
        graph_add = Graph(service.store, uri).add
        for triple in new_graph:
            graph_add(triple)

        private_add = Graph(service.store, URIRef(uri+"#private")).add
        private_add((uri, _HAS_IMPL, cls.RDF_MAIN_TYPE))


_HAS_IMPL = RDFREST.hasImplementation
_RDF_TYPE = RDF.type
