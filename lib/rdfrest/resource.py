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

Note that in strict REST, every URI identifies a different
resource. Query-strings (the part of the URI after the '?') are not an
exception: ``http://a.b/c/d`` and ``http://a.b/c/d?e=f`` are two
different resources. In practice however, URIs that differ only by
their query-string usually identify resources that are closely related
(if not "variants" of the same resource).  RDF-REST endorses this
practice by requiring that the `uri` passed to :class:`Resource` is
stripped from the query-string; the query-string has to be parsed and
passed as `parameters` to the methods :meth:`Resource.rdf_get`,
:meth:`Resource.rdf_put`, :meth:`Resource.rdf_post` and
:meth:`Resource.rdf_delete`.

Hence, an instance of :class:`Resource` handling parameters is really
managing a family or related resources.
"""
from rdflib import Graph, RDFS, URIRef
from rdflib.graph import ReadOnlyGraphAggregate

from rdfrest.exceptions import InvalidDataError, InvalidParametersError, \
    MethodNotAllowedError
from rdfrest.namespaces import RDFREST
from rdfrest.utils import make_fresh_resource

class Resource(object):
    """
    I provide core functionalities for implementing
    :class:`~rdflib.service.Service` resources.

    :param service: the service this resource is a part of
    :type  service: rdfrest.service.Service
    :param uri:     the resource URI (without query-string, see below)
    :type  uri:     rdflib.URIRef

    """

    # subclasses must override this attribute; see Service.register
    MAIN_RDF_TYPE = RDFS.Resource # just to please pylint really

    def __init__(self, service, uri):
        assert isinstance(uri, URIRef), repr(uri)
        self.service = service
        self.uri = uri
        store = service.store
        self._graph = Graph(store, uri)
        self._private = Graph(store, URIRef(uri+"#private"))

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
        overload :method:`check_new_graph` and :method:`store_new_graph` on
        which this method relies.
        """
        errors = cls.check_new_graph(uri, new_graph)
        if errors is not None:
            raise InvalidDataError(errors)
        cls.store_new_graph(service, uri, new_graph)
        return cls(service, uri)

    @classmethod
    def check_new_graph(cls, uri, new_graph,
                        resource=None, added=None, removed=None):
        """Check that a graph is a valid representation of this resource class.

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
        """

    @classmethod
    def store_new_graph(cls, service, uri, new_graph):
        """Store data in order to create a new resource in the service.

        This method *should not* be used directly; it is invoked by
        :meth:`create`, and can be overloaded by subclasses.

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
        """
        assert isinstance(uri, URIRef)
        graph_add = Graph(service.store, uri).add
        for triple in new_graph:
            graph_add(triple)

        private_add = Graph(service.store, URIRef(uri+"#private")).add
        private_add((uri, _HAS_IMPL, cls.MAIN_RDF_TYPE))

    @classmethod
    def mint_uri(cls, target, new_graph, created):
        """Mint a URI for a resource of that class.

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

    def rdf_get(self, parameters=None):
        """Return the graph describing this resource.

        More precisely, the returned graph describes the resource
        identified by the URI `<self.uri>?<parameters>` .

        :param parameters: the query string parameters
        :type  parameters: dict

        :rtype: rdflib.Graph
        :raise: :class:`~rdfrest.exceptions.InvalidParametersError`

        The default behaviour is to accept no `parameters`.
        """
        if not parameters:
            return ReadOnlyGraphAggregate([self._graph])
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

_HAS_IMPL = RDFREST.hasImplementation
