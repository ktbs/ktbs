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
I implement :class:`.interface.ICore` over HTTP.
"""
import atexit
from contextlib import contextmanager
from tempfile import mkdtemp
from weakref import WeakValueDictionary

from httplib2 import Http
from os import listdir, rmdir, unlink
from os.path import exists, isdir, join
from rdflib import Graph, RDF

from ..exceptions import CanNotProceedError, InvalidDataError, \
    InvalidParametersError, MethodNotAllowedError, RdfRestException
from ..cores import ICore
from ..util.proxystore import ProxyStore, ResourceAccessError
from ..wrappers import get_wrapped
from ..util import add_uri_params, coerce_to_uri, ReadOnlyGraph
from .factory import register_implementation
from .hosted import HostedCore




# fix a bug(?) in httplib2 preventing *any* retry;
# some servers (e.g. uWSGI) are quite hasty to close sockets,
# so it is important that some amount of retry be performed
import httplib2
httplib2.RETRIES += 1 # prevents spurious socket.errors with uWSGI


# HTTPLIB2_OPTIONS can be customized 
_HTTPLIB2_OPTIONS = {}
_HTTPLIB2_CREDENTIALS = []
_HTTPLIB2_CERTIFICATES = []

def set_http_option(key, value):
    """I set an option for future HTTP connexions.

    Those options will be passed to httplib2.Http for all future HttpClientCores.
    Note that resources can be cached, so it is only safe to call this function
    before any resource is created.
    """
    _HTTPLIB2_OPTIONS[key] = value

def add_http_credentials(username, password):
    """I add credentials to future HTTP connexions.

    Those credentials will be added to the underlying httplib2.Http
    of all future HttpClientCores.
    Note that resources can be cached, so it is only safe to call this function
    before any resource is created.
    """
    _HTTPLIB2_CREDENTIALS.append((username, password))

def add_http_certificate(key, cert, domain):
    """I add a certificate to future HTTP connexions.

    Those credentials will be added to the underlying httplib2.Http
    of all future HttpClientCores.
    Note that resources can be cached, so it is only safe to call this function
    before any resource is created.
    """
    _HTTPLIB2_CREDENTIALS.append((key, cert, domain))
    
def _http():
    """Shortcut for httplib2.Http with module-specific options."""
    ret = Http(**_HTTPLIB2_OPTIONS)
    for username, password in _HTTPLIB2_CREDENTIALS:
        ret.add_credentials(username, password)
    for key, cert, domain in _HTTPLIB2_CERTIFICATES:
        ret.add_certificate(key, cert, credentials)
    return ret

@register_implementation("http://")
@register_implementation("https://")
class HttpClientCore(ICore):
    """
    A RESTful resource over HTTP

    :param uri: this resource's URI

    .. attribute:: uri

        I implement :attr:`.interface.ICore.uri`.

        I hold this resource's URI as defined at `__init__` time.
    """

    @classmethod
    @HostedCore.handle_fragments
    def factory(cls, uri, _rdf_type=None, _no_spawn=False):
        """I implement :meth:`.interface.ICore.factory`.

        Note that I implement it as a class method, so a first resource can be
        created from its URI without prior knowledge with::

            res = HttpClientCore.factory(uri)

        Note also that `_rdf_type` is ignored.

        :rtype: :class:`HttpClientCore` or :class:`~.hosted.HostedCore`

        NB: if uri contains a fragment-id, the returned resource will be a
        `~.hosted.HostedCore`:class: hosted by a `HttpClientCore`:class: .
        """
        uri = coerce_to_uri(uri)
        resource = _RESOURCE_CACHE.get(uri)
        if resource is None  and  not _no_spawn:
            graph = types = py_class = None
            try:
                graph = Graph(ProxyStore(identifier=uri,
                                         configuration={"httpcx" : _http()}),
                              identifier=uri)
                types = list(graph.objects(uri, RDF.type))
            except ResourceAccessError:
                return None
            if _rdf_type is not None and _rdf_type not in types:
                types.append(_rdf_type)
            py_class = get_wrapped(HttpClientCore, types)
            # use HttpClientCore above and *not* cls, as cls may already
            # be a class produced by get_wrapped
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
            graph = Graph(ProxyStore(identifier=uri,
                                     configuration={"httpcx" : _http()}),
                          identifier=uri)
            # TODO LATER implement a module-level keyring system,
            # so that credentials can be passed to ProxyStore
        self.uri = coerce_to_uri(uri)
        self._http = graph.store.httpserver
        self._state = graph
        if __debug__:
            self._readonly_state = ReadOnlyGraph(graph)
        # NB: self._state is so named to be different from
        # .local.LocalCore._graph ; this is in order to detect bugs:
        #
        # Imagine a mix-in class using the _graph attribute instead of the
        # uniform interface; it will work with LocalCore, but fail
        # with HttpClientCore -- and conversely if it uses _state.


    def __str__(self):
        return "<%s>" % self.uri

    def get_state(self, parameters=None):
        """I implement :meth:`.interface.ICore.get_state`.
        """
        if parameters is None:
            if __debug__:
                return self._readonly_state
            else:
                return self._state
        else:
            return self.get_subresource(parameters).get_state()

    def force_state_refresh(self, parameters=None):
        """I implement `interface.ICore.force_state_refresh`.
        """
        if parameters is None:
            self._state.store.force_refresh()
        else:
            return self.get_subresource(parameters).force_state_refresh()

    def edit(self, parameters=None, clear=False, _trust=False):
        """I implement :meth:`.interface.ICore.edit`.
        """
        if parameters is None:
            return self._make_edit_context(clear)
        else:
            return self.get_subresource(parameters).edit(None, clear, _trust)
 
    def post_graph(self, graph, parameters=None,
                   _trust=False, _created=None, _rdf_type=None):
        """I implement :meth:`.interface.ICore.post_graph`.
        """
        if parameters is None:
            content_type, rdflib_format = self._state.store.prefered_format
            data = graph.serialize(format=rdflib_format)
            headers = {
                'content-type': content_type,
                }
            
            rheaders, rcontent = self._http.request(str(self.uri), 'POST',
                                                    data, headers=headers)
            self._http_to_exception(rheaders, rcontent)
            
            self._state.store.force_refresh()
            # TODO LATER decide on a way to handle several created resources
            created_uri = rheaders['location']
            return [created_uri]
        else:
            return self.get_subresource(parameters).post_graph(
                graph, None, _trust, _created, _rdf_type)

    def delete(self, parameters=None, _trust=False):
        """I implement :meth:`.interface.ICore.delete`.
        """
        if parameters is None:
            rheaders, rcontent = self._http.request(str(self.uri), 'DELETE')
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

        CAUTION: this should be maintained consistent
        with exception handling in
        :meth:`.http_server.HttpFrontend._core_call`.
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



# HTTP cache

CACHE_DIR = mkdtemp("http_cache")

def rm_rf(dirname):
    """Recursively remove directory `dirname`.
    """
    if exists(dirname):
        for path in (join(dirname, i) for i in listdir(dirname)):
            if isdir(path):
                rm_rf(path)
            else:
                unlink(path)
        rmdir(dirname)

atexit.register(rm_rf, CACHE_DIR)
