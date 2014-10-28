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
from bisect import insort
from datetime import datetime
from pyparsing import ParseException
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

    .. warning::
    
        RDF-REST is meant to differenciate an empty query-string from no
        query-string at all. However, WSGI does not allow such a
        distinction. This implementation therefore assumes that an empty
        query-string is no query-string at all.

    """

    def __init__(self, service, service_config):
        """See class docstring.

        :param service: the service to expose over HTTP
        :type  service: :class:`.local.Service`

        :param service_config: An object containing kTBS configuration options
        :type service_config: configParser object

        Additionally, the following configuration options are recognized:

        - cache_control: either a string to be used as the cache-control
          header field, or a callable accepting a resource and returning
          either None or the value of the cache-control header field.
          Defaults to :func:`cache_half_last_modified`.
        - cors_allow_origin: if provided, cross-domain requests will be
          allowed from the given domains, by implementing
          http://www.w3.org/TR/cors/ .
        - max_bytes (int): the maximum number of bytes that this server
          accepts to serve or to consume.
        - max_triples (int): the maximum number of triples that this server
          accepts to serve or to consume.
        """
        # __init__ not called in mixin #pylint: disable=W0231
        # NB: strange, pylint should recognized it is a mixin...
        self._service = service
        self._middleware_stack_version = None
        self._middleware_stack = None

        cache_control = cache_half_last_modified
        if service_config.getboolean('server', 'no-cache'):
            cache_control = (lambda x: None)
        self.cache_control = cache_control

        if service_config.getint('server', 'max-bytes') >= 0:
            self.max_bytes = service_config.getint('server', 'max-bytes')
        else:
            self.max_bytes = None

        if service_config.getint('server', 'max-triples') >= 0:
            self.max_triples = service_config.getint('server', 'max-triples')
        else:
            self.max_triples = None

        #self.cors_allow_origin = set(
        #    options.pop("cors_allow_origin", "").split(" ")
        #    )
        self.cors_allow_origin = service_config.get('server', 'cors-allow-origin', 1).split(" ")

        # HttpFrondend does not receive a dictionary any more
        # Other options should be explicitely set
        #self._options = options or {}
        self._options = {}

    def __call__(self, environ, start_response):
        """Honnor the WSGI protocol.
        """
        if self._middleware_stack_version != _MIDDLEWARE_STACK_VERSION:
            self._middleware_stack = build_middleware_stack(self._core_call)
            self._middleware_stack_version = _MIDDLEWARE_STACK_VERSION
        return self._middleware_stack(environ, start_response)

    def _core_call(self, environ, start_response):
        """The actual implementation of this WSGI application.

        NB: the __call__ method wraps this function into a middleware_stack,
        including all middlewares registered by plugins.

        CAUTION: the conversion of exceptions to HTTP status codes  should be
        maintained consistent with
        :meth:`.http_client.HttpResource._http_to_exception`.
        """
        request = MyRequest(environ)
        resource_uri, request.uri_extension = extsplit(request.path_url)
        resource_uri = URIRef(resource_uri)
        resource = self._service.get(resource_uri)
        if resource is None:
            resp = self.issue_error(404, request, None)
            return resp(environ, start_response)
        if resource.uri != resource_uri:
            resp = self.issue_error(303, request, None,
                                    location=str(resource.uri))
            return resp(environ, start_response)
        method = getattr(self, "http_%s" % request.method.lower(), None)
        if method is None:
            resp = self.issue_error(405, request, resource,
                                    allow="HEAD, GET, PUT, POST, DELETE")
            return resp(environ, start_response)
        try:
            with self._service:
                resource.force_state_refresh()
                pre_process_request(self._service, request, resource)
                response = method(request, resource)
                # NB: even for a GET, we embed method in a "transaction"
                # because it may nonetheless make some changes (e.g. in
                # the #metadata graphs)
        except HttpException, ex:
            response = ex.get_response(request)
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
        except ParseException, ex:
            status = "400 Bad Request"
            message = "%s at line %s col %s\n\n%s" % \
                      (ex.msg, ex.lineno, ex.column, ex.markInputline())
            response = MyResponse("%s - Parse exception\n%s"
                                  % (status, message),
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
                response.headerlist.extend([
                    ("access-control-allow-origin", origin),
                    ("access-control-allow-methods",
                     "GET, HEAD, PUT, POST, DELETE"),
                    ("access-control-allow-credentials", "true"),
                ])
                acrh = request.headers.get("access-control-request-headers")
                if acrh:
                    response.headerlist.append(
                        ("access-control-allow-headers", acrh),
                        )
            
        return response(environ, start_response)

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
        ext = request.uri_extension
        if ext:
            parser = None
            _, ctype = get_serializer_by_extension(ext)
            if ctype is not None:
                parser, _ = get_parser_by_content_type(ctype)
            if parser is None:
                return self.issue_error(404, request, resource, "Bad extension")
            print "===", parser
        else:
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

class SparqlHttpFrontend(HttpFrontend):
    """
    I derive :class:`HttpFrontend` by adding support for the SPARQL protocol.
    """

    POST_CTYPES = {"application/x-www-form-urlencoded", "application/sparql-query"}

    def http_get(self, request, resource):
        if request.GET.getall("query"):
            return self.handle_sparql(request, resource)
        else:
            return super(SparqlHttpFrontend, self).http_get(request, resource)

    def http_post(self, request, resource):
        if request.content_type in self.POST_CTYPES:
            return self.handle_sparql(request, resource)
        else:
            return super(SparqlHttpFrontend, self).http_post(request, resource)

    def handle_sparql(self, request, resource):
        """
        I handle a SPARQL request
        """
        if request.method == "GET" \
        or request.content_type == "application/sparql-query":
            params = request.GET
        else:
            params = request.POST
        default_graph_uri = params.getall("default-graph-uri")
        named_graph_uri = params.getall("named-graph-uri")

        if request.content_type != "application/sparql-query":
            lst = params.getall("query")
            if len(lst) == 0:
                # NB: not rejecting several queries, because some services
                # provide the same query several times (YASGUI)
                return MyResponse("400 Bad Request\nQuery not provided",
                                  status="400 Bad Request",
                                  request=request)
            query = lst[0]
        else:
            query = request.body

        # TODO LATER do something with default_graph_uri and named_graph_uri ?

        resource.force_state_refresh()
        graph = resource.get_state()
        result = graph.query(query)
        # TODO LATER use content negociation to decide on the output format
        if result.graph is not None:
            serfmt = "xml"
            ctype = "application/rdf+xml"
        else:
            serfmt = "json"
            ctype = "application/sparql-results+json"
        return MyResponse(result.serialize(format=serfmt),
                          status="200 Ok",
                          content_type=ctype,
                          request=request)



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

class HttpException(Exception):
    def __init__(self, message, status, **headers):
        super(HttpException, self).__init__(message)
        self.status = status
        self.headers = headers

    def get_body(self):
        return "%s\n%s" % (self.status, self.message)

    def get_headerlist(self):
        hlist = []
        for key, val in self.headers.iteritems():
            if type(val) is not list:
                val = [val]
            for i in val:
                hlist.append((str(key), str(i)))
        return  hlist

    def get_response(self, request):
        return MyResponse(body=self.get_body(),
                          status=self.status,
                          headerlist=self.get_headerlist(),
                          request=request)


class UnauthorizedError(HttpException):
    """An error raised when a remote user is not authorized to perform an
    action.
    """
    def __init__(self, message="", challenge=None, **headers):
        if challenge is None:
            challenge = 'Basic Realm="authentication required"'
        headers['www-authenticate'] = challenge
        super(UnauthorizedError, self).__init__(message,
                                                "401 Unauthorized",
                                                **headers)

class RedirectException(HttpException):
    """An exception raised to redirect a given query to another URL.
    """
    def __init__(self, location, code=303, **headers):
        self.message = "Redirecting to <%s>" % location
        self.status = "%s Redirect" % code
        headers['location'] = location
        super(RedirectException, self).__init__(self.message, self.status, **headers)

    def get_body(self):
        return "{0} - Can not proceed\n{1}".format(self.status, self.message)

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

###############################################################
#
# UWSGI Middleware registry
#

_MIDDLEWARE_REGISTRY = []
_MIDDLEWARE_STACK_VERSION = 0

def build_middleware_stack(original_application):
    stack = original_application
    for _, middleware in _MIDDLEWARE_REGISTRY[::-1]:
        stack = middleware(stack)
    return stack

def register_middleware(level, middleware, quiet=False):
    """
    Register a middleware for HTTP requests.

    :param level: a level governing the order of execution of pre-processors;
      predefined levels are AUTHENTICATION, AUTHORIZATION

    :param middleware: a function accepting a WSGI application,
      and producing a WSGI application wrapping the former
    """
    if middleware in ( i[1] for i in _MIDDLEWARE_REGISTRY ):
        if not quiet:
            raise ValueError("middleware already registered")
        else:
            return
    insort(_MIDDLEWARE_REGISTRY, (level, middleware))
    global _MIDDLEWARE_STACK_VERSION
    _MIDDLEWARE_STACK_VERSION += 1

def unregister_middleware(middleware, quiet=False):
    """
    Unregister a middleware for HTTP requests.
    """
    for i, pair in enumerate(_MIDDLEWARE_REGISTRY):
        if pair[1] == preproc:
            del _MIDDLEWARE_REGISTRY[i]
            global _MIDDLEWARE_STACK_VERSION
            _MIDDLEWARE_STACK_VERSION += 1
            return
    if not quiet:
        raise ValueError("pre-processor not registered")

###############################################################
#
# Request pre-processors registry
#

_PREPROC_REGISTRY = []

def pre_process_request(service, request, resource):
    """
    Applies all registered pre-processors to `request`.
    """
    for _, plugin in _PREPROC_REGISTRY:
        plugin(service, request, resource)

def register_pre_processor(level, preproc, quiet=False):
    """
    Register a pre-processor for HTTP requests.

    :param level: a level governing the order of execution of pre-processors;
      predefined levels are AUTHENTICATION, AUTHORIZATION

    :param preproc: a function accepting 3 parameters: a Service,
      a Webob request and an RdfRest resource
    """
    if preproc in ( i[1] for i in _PREPROC_REGISTRY ):
        if not quiet:
            raise ValueError("pre-processor already registered")
        else:
            return
    insort(_PREPROC_REGISTRY, (level, preproc))

def unregister_pre_processor(preproc, quiet=False):
    """
    Unregister a pre-processor for HTTP requests.
    """
    for i, pair in enumerate(_PREPROC_REGISTRY):
        if pair[1] == preproc:
            del _PREPROC_REGISTRY[i]
            return
    if not quiet:
        raise ValueError("pre-processor not registered")

SESSION = 0
AUTHENTICATION = 200
AUTHORIZATION = 400
