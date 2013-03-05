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
I implement a WSGI-based HTTP server wrapping a given :class:`.local.Service`.
"""
from datetime import datetime
from rdflib import URIRef
from time import time
from webob import Request, Response
from webob.etag import AnyETag, etag_property
from webob.response import status_reasons

from .exceptions import CanNotProceedError, InvalidDataError, \
    InvalidParametersError, MethodNotAllowedError, ParseError, \
    RdfRestException, SerializeError
from .iso8601 import UTC
from .parsers import get_parser_by_content_type
from .serializers import get_serializer_by_content_type, \
    get_serializer_by_extension, iter_serializers
from .utils import extsplit

class MyRequest(Request):
    """I override webob.Request by allowing weak etags.
    """
    if_match = etag_property('HTTP_IF_MATCH', AnyETag, '14.24', strong=False)

class MyResponse(Response):
    """I override webob.Response's default behaviour.
    """
    default_content_type = "text/plain"
    default_conditional_response = True

class HttpFrontend(object):
    """The role of the WSGI front-end is to relay requests to and response
    from the service through the HTTP protocol.

    For parsing and serializing payloads to and from RDF graphs, HttpFrontend
    relies on the functions registered in `.local.parsers`:mod: and
    `.local.serializers`:mod:.
    
    In the future, WsgiFrontent may also include on-the-fly translation of
    contents, for changing internal URIs into URIs served by the
    HttpFrontend.

    :param service: the service to expose over HTTP
    :type  service: :class:`.local.Service`

    Additionally, the following keyword arguments are recognized:

    :param cache_control: either a string to be used as the cache-control header
                          field, or a callable accepting a resource and
                          returning either None or the value of the
                          cache-control header field.
                          Defaults to :func:`cache_half_last_modified`.
    :param max_bytes:     the maximum number of bytes that this server accepts
                          to serve or to consume.
    :type  max_bytes:     int
    :param max_triples:   the maximum number of triples that this server accepts
                          to serve or to consume.
    :type  max_triples:   int

    .. warning::
    
        RDF-REST is meant to differenciate an empty query-string from no
        query-string at all. However, WSGI does not allow such a
        distinction. This implementation therefore assumes that an empty
        query-string is no query-string at all.

    """

    def __init__(self, service, **options):
        """See class docstring.
        """
        # __init__ not called in mixin #pylint: disable=W0231
        # NB: strange, pylint should recognized it is a mixin...
        self._service = service
        cache_control = options.pop("cache_control", cache_half_last_modified)
        if isinstance(cache_control, basestring):
            cache_control = (lambda _, ret = cache_control: ret)
        self.cache_control = cache_control
        self.max_bytes = options.pop("max_bytes", None)
        self.max_triples = options.pop("max_triples", None)
        self.cors_allow_origin = set(
            options.pop("cors_allow_origin", "").split(" ")
            )
        self._options = options or {}

    def __call__(self, environ, start_response):
        """Wrap `get_response` to honnor the WSGI protocol.
        """
        request = MyRequest(environ)
        response = self.get_response(request)
        return response(environ, start_response)
        
    def get_response(self, request):
        """Process a webob request and return a webob response.

        :param request: a MyRequest

        CAUTION: the conversion of exceptions to HTTP status codes  should be
        maintained consistent with
        :meth:`.http_client.HttpResource._http_to_exception`.
        """
        resource_uri, request.uri_extension = extsplit(request.path_url)
        resource_uri = URIRef(resource_uri)
        resource = self._service.get(resource_uri)
        if resource is None:
            return self.issue_error(404, request, None)
        if resource.uri != resource_uri:
            return self.issue_error(303, request, None,
                                    location=str(resource.uri))
        method = getattr(self, "http_%s" % request.method.lower(), None)
        if method is None:
            return self.issue_error(405, request, resource,
                                    allow="HEAD, GET, PUT, POST, DELETE")
        try:
            with self._service:
                response = method(request, resource)
                # NB: even for a GET, we embed method in a "transaction"
                # because it may nonetheless make some changes (e.g. in
                # the #metadata graphs)
        except CanNotProceedError, ex:
            status = "409 Conflict"
            response = MyResponse("%s - Can not proceed\n%s"
                                  % (status, ex.message),
                                  status=status,
                                  request=request)
        except InvalidDataError, ex:
            status = "403 Forbidden"
            response = MyResponse("%s - Invalid data\n%s"
                                  % (status, ex.message),
                                  status=status,
                                  request=request)
        except InvalidParametersError, ex:
            status = "404 Not Found"
            response = MyResponse("%s - Invalid parameters\n%s"
                                  % (status, ex.message),
                                  status=status,
                                  request=request)
        except MethodNotAllowedError, ex:
            status = "405 Method Not Allowed"
            response = MyResponse("%s\n%s" % (status, ex.message),
                                  status=status,
                                  request=request)
            # TODO LATER find a nice way to populate response.allow ?
        except ParseError, ex:
            status = "400 Bad Request"
            response = MyResponse("%s - Parse error\n%s"
                                  % (status, ex.message),
                                  status=status,
                                  request=request)
        except SerializeError, ex:
            status = "550 Serialize Error"
            response = MyResponse("%s\n%s" % (status, ex.message),
                                  status=status,
                                  request=request)
        except RdfRestException, ex:
            status = "500 Internal Error"
            response = MyResponse("%s - Other RDF-REST exception\n%s"
                                  % (status, ex.message),
                                  status=status,
                                  request=request)

        cache_control = self.cache_control(resource)
        if cache_control:
            response.cache_control = cache_control
        if self.cors_allow_origin:
            origin = request.headers.get("origin")
            if origin and (origin in self.cors_allow_origin
                           or "*" in self.cors_allow_origin):
                response.headerlist.append(
                    ("access-control-allow-origin", origin)
                    ),
                response.headerlist.append(
                    ("access-control-allow-methods",
                     "GET HEAD PUT POST DELETE"),
                    )
                acrh = request.headers.get("access-control-request-headers")
                if acrh:
                    response.headerlist.append(
                        ("access-control-allow-headers", acrh),
                        )
            
        return response

    def http_delete(self, request, resource):
        """Process a DELETE request on the given resource.
        """
        # method could be a function #pylint: disable=R0201
        # TODO LATER how can we transmit context (authorization? anything else?)
        resource.delete(request.GET.mixed() or None)
        return MyResponse(status="204 Resource deleted", request=request)

    def http_get(self, request, resource):
        """Process a GET request on the given resource.
        """
        # find serializer
        rdf_type = resource.RDF_MAIN_TYPE
        ext = request.uri_extension
        if ext:
            serializer, ctype = get_serializer_by_extension(ext, rdf_type)
            if serializer is None:
                return self.issue_error(404, request, resource, "Bad extension")
        else:
            serializer = None
            ctype = request.accept.best_match( 
                ser[1] for ser in iter_serializers(rdf_type) )
            if ctype is None:
                # 406 Not Acceptable
                version_list = []
                for _, ctype, ext in iter_serializers(rdf_type):
                    if ext:
                        version_list.append("%s <%s.%s>"
                                            % (ctype, resource.uri, ext))
                    else:
                        version_list.append(ctype)
                return MyResponse("\n".join(version_list),
                                  status="406 Not Acceptable",
                                  request=request)
            # else we can be certain that the serializer exists, so:
            serializer, ext = get_serializer_by_content_type(ctype, rdf_type)

        # populate response header according to serializer
        headerlist = []
        if ctype[:5] == "text/":
            headerlist.append(("content-type", ctype+";charset=utf-8"))
        else:
            headerlist.append(("content-type", ctype))
        if ext is not None:
            headerlist.append(("content-location",
                               str("%s.%s" % (resource.uri, ext))))
        iter_etags = getattr(resource, "iter_etags", None)
        if iter_etags is not None:
            etags = " ".join( 'W/"%s"' % taint_etag(i, ctype)
                              for i in iter_etags(request.GET.mixed() or None) )
            headerlist.append(("etag", etags))
        last_modified = getattr(resource, "last_modified", None)
        if last_modified is not None:
            last_modified = datetime.fromtimestamp(last_modified, UTC)
            headerlist.append(("last-modified", last_modified.isoformat()))

        # get graph and redirect if needed
        graph = resource.get_state(request.GET.mixed() or None)
        redirect = getattr(graph, "redirect_to", None)
        if redirect is not None:
            return self.issue_error(303, request, None,
                                    location=redirect)

        # check triples & bytes limitations and serialize
        if self.max_triples is not None  and  len(graph) > self.max_triples:
            return self.issue_error(403, request, resource,
                                    "max_triple (%s) was exceeded"
                                    % self.max_triples )
        app_iter = serializer(graph, resource)
        if self.max_bytes is not None:
            # TODO LATER find a better way to guess the number of bytes?
            payload = "".join(app_iter)
            if len(payload) >  self.max_bytes:
                return self.issue_error(403, request, resource,
                                        "max_bytes (%s) was exceeded"
                                        % self.max_bytes )
            app_iter = [payload]

        return MyResponse(headerlist=headerlist, app_iter=app_iter)

    def http_head(self, request, resource):
        """Process a HEAD request on the given resource.
        """
        response = self.http_get(request, resource)
        return MyResponse(status=response.status,
                           headerlist=response.headerlist, request=request)

    def http_options(self, request, resource):
        """Process an OPTIONS request on the given resource.
        """
        # 
        headerlist = [
            ("allow", "GET, HEAD, PUT, POST, DELETE"),
            ]
        return MyResponse(headerlist=headerlist, request=request)

    def http_post(self, request, resource):
        """Process a POST request on the given resource.
        """
        parser, _ = get_parser_by_content_type(request.content_type
                                               or "text/turtle")
        if parser is None:
            return self.issue_error(415, request, resource)
        if self.max_bytes is not None:
            length = request.content_length
            if length is None:
                return self.issue_error(411, request, resource) #length required
            elif length > self.max_bytes:
                return self.issue_error(413, request, resource,
                                        "max_bytes (%s) was exceeded"
                                        % self.max_bytes)
        graph = parser(request.body, resource.uri, request.charset)
        if self.max_triples is not None:
            if len(graph) > self.max_triples:
                return self.issue_error(413, request, resource,
                                        "max_triples (%s) was exceeded"
                                        % self.max_triples)
        results = resource.post_graph(graph, request.GET.mixed() or None)
        if not results:
            return MyResponse(status=205, request=request) # Reset
        else:
            content = "\n".join(results)
            headerlist = [
                ("location", str(results[0])),
                ]
            return MyResponse(content, status=201, headerlist=headerlist,
                               request=request) # Created

    def http_put(self, request, resource):
        """Process a PUT request on the given resource.

        .. note::

            If `resource` has an `iter_etags` properties, then it is
            required that `request` include an ``If-Match`` header
            field. Note that those etags are *weak* etags (see
            :class:`~rdfrest.mixins.BookkeepingMixin`), which are not
            allowed in ``If-Match`` according to :RFC:`2616`. However,
            this limitation will probably be dropped in future
            versions of HTTP, so do not follow it.
        """
        # too many return statements (7/6) #pylint: disable=R0911

        # find parser
        ctype = request.content_type or "text/turtle"
        iter_etags = getattr(resource, "iter_etags", None)
        if iter_etags is not None:
            if request.headers.get("if-match", "*") == "*":
                return MyResponse(
                    status="403 Forbidden: 'if-match' is required",
                    request=request,
                    )
            for i in iter_etags(request.GET.mixed() or None):
                if taint_etag(i, ctype) in request.if_match:
                    break
            else: # no matching etag found in 'for' loop
                return self.issue_error(412, request, resource)
        parser, _ = get_parser_by_content_type(ctype)

        # parse and check bytes/triples limitations
        if parser is None:
            return self.issue_error(415, request, resource)
        if self.max_bytes is not None:
            length = request.content_length
            if length is None:
                return self.issue_error(411, request, resource) #length required
            elif length > self.max_bytes:
                return self.issue_error(413, request, resource,
                                        "max_bytes (%s) was exceeded"
                                        % self.max_bytes)
        try:
            with resource.edit(request.GET.mixed() or None, True) as graph:
                parser(request.body, resource.uri, request.charset, graph)
                if self.max_triples is not None:
                    if len(graph) > self.max_triples:
                        raise _TooManyTriples
                        # ensures that we exit the edit context without
                        # commiting
        except _TooManyTriples:
            return self.issue_error(413, request, resource,
                                    "max_triples (%s) was exceeded"
                                    % self.max_triples)
            
        return self.http_get(request, resource)

    def issue_error(self, status, request, resource, message=None, **kw):
        """Issues an HTTP error.

        :param status:   the HTTP status
        :type  status:   int
        :param request:  the request being processed
        :type  request:  MyRequest
        :param resource: the resource being addressed (can be None)
        :type  resource: rdfrest.local.ILocalResource
        :param message:  the payload of the error response
        :type  message:  str
        :param kw:       header fields to add to the response

        Can be overridden by subclasses to provide custom error messages.
        """
        # this method is intended to be overridden, so the following pylint
        # errors are not relevant:
        # * method could be a function #pylint: disable=R0201 
        # * unsued argument            #pylint: disable=W0613

        status = "%s %s" % (status, status_reasons[status])
        body = status
        if message is None:
            body = "%s\n%s" % (body, message)
        res = MyResponse(body, status, kw.items())
        return res

def taint_etag(etag, ctype):
    """I taint etag with the given content-type.

    This is required because caches may be smart with different entities of the
    same resources, as described in RFC 2616, sec 13.6.
    """
    return "%s/%s" % (ctype, etag)
    # TODO LATER make a more opaque (unreversible?) tainting operation?

class _TooManyTriples(Exception):
    """This exception class is used to abort edit context during PUT.
    """
    pass

################################################################
#
# Cache-control functions
#

def cache_half_last_modified(resource):
    """I use last-modified to provide cache-control directive.

    If resource has a last_modified property (assumed to return a number of
    seconds since EPOCH), I allow to cache resource for half the time since
    it was last modified.

    Else, I return None.
    """
    last_mod = getattr(resource, "last_modified", None)
    if last_mod is not None:
        return "max-age=%s" % (int(time() - last_mod) / 2)
    else:
        return None
