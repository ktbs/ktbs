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
I implement :class:`.interface.IResource` over HTTP.
"""
from contextlib import contextmanager
from httplib2 import Http
from rdflib import Graph, RDF
from weakref import WeakValueDictionary

from .exceptions import CanNotProceedError, InvalidDataError, \
    InvalidParametersError, MethodNotAllowedError, RdfRestException
from .factory import register_implementation
from .interface import get_subclass, IResource
from .hosted import HostedResource
from .proxystore import ProxyStore, ResourceAccessError
from .utils import add_uri_params, coerce_to_uri, ReadOnlyGraph

@register_implementation("http://")
class HttpResource(IResource):
    """
    A RESTful resource over HTTP

    :param uri: this resource's URI

    .. attribute:: uri

        I implement :attr:`.interface.IResource.uri`.

        I hold this resource's URI as defined at `__init__` time.
    """

    @classmethod
    @HostedResource.handle_fragments
    def factory(cls, uri, _rdf_type=None, _no_spawn=False):
        """I implement :meth:`.interface.IResource.factory`.

        Note that I implement it as a class method, so a first resource can be
        created from its URI without prior knowledge with::

            res = HttpResource.factory(uri)

        Note also that `_rdf_type` is ignored.

        :rtype: :class:`HttpResource` or :class:`~.hosted.HostedResource`

        NB: if uri contains a fragment-id, the returned resource will be a
        `~.hosted.HostedResource`:class: hosted by a `HttpResource`:class: .
        """
        uri = coerce_to_uri(uri)
        resource = _RESOURCE_CACHE.get(uri)
        if resource is None  and  not _no_spawn:
            graph = types = py_class = None
            try:
                graph = Graph(ProxyStore(identifier=uri), identifier=uri)
                types = list(graph.objects(uri, RDF.type))
            except ResourceAccessError:
                return None
            if _rdf_type is not None and _rdf_type not in types:
                types.append(_rdf_type)
            py_class = get_subclass(HttpResource, types)
            # use HttpResource above and *not* cls, as cls may already
            # be a class produced by get_subclass
            resource = py_class(uri, graph)
            _RESOURCE_CACHE[uri] = resource
        return resource

    def __init__(self, uri, graph=None):
        """Create a new http_client resource.
        """
        # not calling parents __init__ #pylint: disable=W0231
        uri = coerce_to_uri(uri)
        assert (graph is None or (
                isinstance(graph.store, ProxyStore) and
                graph.store._identifier == uri # friend #pylint: disable=W0212
                )), "unexpected provided graph"

        if graph is None:
            graph = Graph(ProxyStore(identifier=uri), identifier=uri)
            # TODO LATER implement a module-level keyring system,
            # so that credentials can be passed to ProxyStore
        self.uri = coerce_to_uri(uri)
        self._state = graph
        if __debug__:
            self._readonly_state = ReadOnlyGraph(graph)
        # NB: self._state is so named to be different from
        # .local.StandaloneResource._graph ; this is in order to detect bugs:
        #
        # Imagine a mix-in class using the _graph attribute instead of the
        # uniform interface; it will work with StandaloneResource, but fail
        # with HttpResource -- and conversely if it uses _state.

    def __str__(self):
        return "<%s>" % self.uri

    def get_state(self, parameters=None):
        """I implement :meth:`.interface.IResource.get_state`.
        """
        if parameters is None:
            if __debug__:
                return self._readonly_state
            else:
                return self._state
        else:
            return self.get_subresource(parameters).get_state()

    def force_state_refresh(self, parameters=None):
        """I implement `interface.IResource.force_state_refresh`.
        """
        if parameters is None:
            self._state.store.force_refresh()
        else:
            return self.get_subresource(parameters).force_state_refresh()

    def edit(self, parameters=None, clear=False, _trust=False):
        """I implement :meth:`.interface.IResource.edit`.
        """
        if parameters is None:
            return self._make_edit_context(clear)
        else:
            return self.get_subresource(parameters).edit(None, clear, _trust)
 
    def post_graph(self, graph, parameters=None,
                   _trust=False, _created=None, _rdf_type=None):
        """I implement :meth:`.interface.IResource.post_graph`.
        """
        if parameters is None:
            content_type, rdflib_format = self._state.store.prefered_format
            data = graph.serialize(format=rdflib_format)
            headers = {
                'content-type': content_type,
                }
            
            rheaders, rcontent = Http().request(str(self.uri), 'POST', data,
                                                headers=headers)
            self._http_to_exception(rheaders, rcontent)
            
            self._state.store.force_refresh()
            # TODO LATER decide on a way to handle several created resources
            created_uri = rheaders['location']
            return [created_uri]
        else:
            return self.get_subresource(parameters).post_graph(
                graph, None, _trust, _created, _rdf_type)

    def delete(self, parameters=None, _trust=False):
        """I implement :meth:`.interface.IResource.delete`.
        """
        if parameters is None:
            rheaders, rcontent = Http().request(str(self.uri), 'DELETE')
            self._http_to_exception(rheaders, rcontent)
        else:
            return self.get_subresource(parameters).delete(None, _trust)
        

    ################################################################
    #
    # Other public method spefific to this implementation
    #

    def get_subresource(self, parameters):
        """I return version of this resource with additional parameters.

        I raise :class:`~.exceptions.InvalidParametersError` if that resource
        can not be constructed.
        """
        uri = add_uri_params(self.uri, parameters)
        try:
            subresource = self.factory(uri)
        except ResourceAccessError, ex:
            raise InvalidParametersError(ex)
        if subresource is None:
            raise InvalidParametersError("factory returned None")
        return subresource

    ################################################################
    #
    # Private methods
    #

    @contextmanager
    def _make_edit_context(self, clear):
        """I make the edit context required by :meth:`edit`.
        """
        try:
            if clear:
                self._state.remove((None, None, None))
            yield self._state
            self._state.store.commit() # PUTs the changes through HTTP
        except BaseException:
            self._state.store.rollback() # revert to remote state

    @classmethod
    def _http_to_exception(cls, headers, content):
        """I inspect HTTP headers and raise an appropriate exception if needed.

        CAUTION: this should be maintained consistent with
        :meth:`.http_server.HttpFrontend.get_response`.
        """
        status = headers.status
        if status / 100 == 2:
            return
        elif status == 403:
            raise InvalidDataError(content)
        elif status == 404:
            raise InvalidParametersError(content)
        elif status == 405:
            raise MethodNotAllowedError(content)
        elif status == 409:
            raise CanNotProceedError(content)
        else:
            raise RdfRestException(content)


_RESOURCE_CACHE = WeakValueDictionary()
# this is not per se a cache, but ensure that we will not generate multiple
# instances for the same resource; this limits the risk of having a resource
# becoming stale because another instance with the same URI has made changes.
# Note that the risk still exists if the changes are made by another process.
