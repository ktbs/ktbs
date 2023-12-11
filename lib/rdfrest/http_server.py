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
I implement a WSGI-based HTTP server
wrapping a given :class:`.cores.local.Service`.
"""
from bisect import insort
from contextlib import closing
from time import time

from pyparsing import ParseException
from rdflib import URIRef
from webob import Request, Response
from webob.etag import AnyETag, etag_property

from webob.response import status_reasons

from datetime import datetime
from .exceptions import CanNotProceedError, InvalidDataError, \
    InvalidParametersError, MethodNotAllowedError, ParseError, \
    RdfRestException, SerializeError
from .util.iso8601 import UTC
from .parsers import get_parser_by_content_type
from .serializers import get_serializer_by_content_type, \
    get_serializer_by_extension, iter_serializers
from .util import extsplit

from logging import getLogger
import traceback

LOG = getLogger(__name__)

class MyRequest(Request):
    """I override webob.Request by allowing weak etags.
    """
    if_match = etag_property('HTTP_IF_MATCH', AnyETag, '14.24', strong=False)

class MyResponse(Response):
    """I override webob.Response's default behaviour.
    """
    default_content_type = "text/plain"
    default_conditional_response = True

    def __init__(self, body=None, status=None, headerlist=None, **kw):
        if 'charset' not in kw:
            kw['charset'] = 'utf-8'
        Response.__init__(self, body, status, headerlist, **kw)

class HttpFrontend(object):
    """The role of the WSGI front-end is to relay requests to and response
    from the service through the HTTP protocol.

    For parsing and serializing payloads to and from RDF graphs, HttpFrontend
    relies on the functions registered in `.cores.local.parsers`:mod: and
    `.cores.local.serializers`:mod:.

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
        :type  service: :class:`.cores.local.Service`

        :param service_config: An object containing kTBS configuration options
        :type service_config: configParser object

        Additionally, the following configuration options are recognized:

        - cache_control: a string to be used as the cache-control header field,
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

        self.cache_control = 'max-age=1'
        if service.config.has_option('server', 'cache-control'):
            self.cache_control = service.config.get('server', 'cache-control')
            if service.config.has_option('server', 'no-cache'):
                LOG.error("Deprecated option no-cache is ignored, "
                          "as it is overridden by cache-control")
        elif service.config.has_option('server', 'no-cache'):
            LOG.error("Option no-cache is deprecated, use cache-control instead")
            if service.config.getboolean('server', 'no-cache'):
                self.cache_control = ''

        if service_config.getint('server', 'max-bytes') >= 0:
            self.max_bytes = service_config.getint('server', 'max-bytes')
        else:
            self.max_bytes = None

        if service_config.getint('server', 'max-triples') >= 0:
            self.max_triples = service_config.getint('server', 'max-triples')
        else:
            self.max_triples = None

        self.reset_connection = \
            service_config.getboolean('server', 'reset-connection')

        self.send_traceback = \
            service_config.getboolean('server', 'send-traceback')

        # HttpFrondend does not receive a dictionary any more
        # Other options should be explicitely set
        #self._options = options or {}
        self._options = {}

        if self.reset_connection:
            try:
                self._service.store.close()
            except:
                LOG.warning("Ignoring exception when closing store", exc_info=1)
                # seems to happen for no good reason with Virtuoso


    def __call__(self, environ, start_response):
        """Honnor the WSGI protocol.

        CAUTION: the conversion of exceptions to HTTP status codes  should be
        maintained consistent with
        :meth:`.cores.http_client.HttpClientCore._http_to_exception`.
        """
        if self.reset_connection:
            self._service.store.open(self._service.store_config_str)
        try:
            request = Request(environ)
            requested_path, requested_extension = extsplit(request.path_info)
            requested_uri = URIRef("%s%s" % (
                self._service.root_uri[:-1], requested_path))
            resource = self._service.get(requested_uri)
            environ['rdfrest.requested.uri'] = requested_uri
            environ['rdfrest.requested.extension'] = requested_extension
            environ['rdfrest.resource'] = resource
            environ['rdfrest.parameters'] = dict(request.GET.mixed())
            environ['rdfrest.send-traceback'] = self.send_traceback

            if self._middleware_stack_version != _MIDDLEWARE_STACK_VERSION:
                self._middleware_stack = build_middleware_stack(self._core_call)
                self._middleware_stack_version = _MIDDLEWARE_STACK_VERSION

            return self._middleware_stack(environ, start_response)
        finally:
            if self.reset_connection:
                self._service.store.close()


    def _core_call(self, environ, start_response):
        """The actual implementation of this WSGI application.

        NB: the __call__ method wraps this function into a middleware_stack,
        including all middlewares registered by plugins.
        """
        request = MyRequest(environ)
        resource = environ['rdfrest.resource']
        resource_uri = environ['rdfrest.requested.uri']
        request.uri_extension = environ['rdfrest.requested.extension']

        if resource is None:
            resp = self.issue_error(404, request, None)
            return resp(environ, start_response)
        method = getattr(self, "http_%s" % request.method.lower(), None)
        if method is None:
            resp = self.issue_error(405, request, resource,
                                    allow="HEAD, GET, PUT, POST, DELETE, OPTIONS")
            return resp(environ, start_response)

        pre_process_request(self._service, request, resource)
        response = method(request, resource)
        return response(environ, start_response)

    def http_delete(self, request, resource):
        """Process a DELETE request on the given resource.
        """
        # method could be a function #pylint: disable=R0201
        # TODO LATER how can we transmit context (authorization? anything else?)
        with self._service:
            resource.delete(request.environ['rdfrest.parameters'] or None)
        return MyResponse(status="204 Resource deleted", request=request)

    def http_get(self, request, resource):
        """Process a GET request on the given resource.
        """
        headerlist = []
        params = request.environ['rdfrest.parameters']

        # find serializer
        rdf_type = resource.RDF_MAIN_TYPE
        ext = request.uri_extension
        if ext:
            serializer, ctype = get_serializer_by_extension(ext, rdf_type)
            if serializer is None:
                return self.issue_error(404, request, resource, "Bad extension")
        else:
            headerlist.append(("vary", "accept"))
            serializer = None
            ctype = best_match(
                request.accept,
                [ ser[1] for ser in iter_serializers(rdf_type) ]
            )
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

        # get graph and redirect if needed
        cache_bypass = params.pop("_", None) # dummy param used by JQuery to invalidate cache
        graph = resource.get_state(params or None)
        redirect = getattr(graph, "redirected_to", None)
        if redirect is not None:
            return self.issue_error(303, request, None,
                                    location=redirect)

        # populate response header according to serializer
        if ctype[:5] == "text/":
            headerlist.append(("content-type", ctype+";charset=utf-8"))
        else:
            headerlist.append(("content-type", ctype))
        if ext is not None:
            headerlist.append(("content-location",
                               str("%s.%s" % (resource.uri, ext))))

        # also insert etags, if available
        etag_list = getattr(graph, "etags", None)
        if etag_list is None:
            iter_etags = getattr(resource, "iter_etags", None)
            if iter_etags is not None:
                etag_list = list(iter_etags(params or None))
        if etag_list:
            etag_list = [ 'W/"%s"' % taint_etag(i, ctype)
                          for i in etag_list ]
            headerlist.append(("etag", etag_list[-1]))
            headerlist.append(("x-etags", " ".join(etag_list)))

        # also insert last-modified, if available
        last_modified = getattr(resource, "last_modified", None)
        if last_modified is not None:
            last_modified = datetime.fromtimestamp(last_modified, UTC)
            headerlist.append(("last-modified", last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')))

        # also insert links (navigation and other) if available
        links = getattr(graph, "links", ())
        for link in links:
            uri = link.pop('uri')
            link_props = ';'.join( '%s="%s"' % item for item in link.items() )
            link_val = '<%s>;%s' % (uri, link_props)
            headerlist.append(("link", link_val))

        # check triples & bytes limitations and serialize
        if self.max_triples is not None  and  len(graph) > self.max_triples:
            return self.issue_error(403, request, resource,
                                    "max_triple (%s) was exceeded"
                                    % self.max_triples )
        app_iter = serializer(graph, resource)
        if self.max_bytes is not None:
            # TODO LATER find a better way to guess the number of bytes?
            payload = b"".join(app_iter)
            if len(payload) >  self.max_bytes:
                return self.issue_error(403, request, resource,
                                        "max_bytes (%s) was exceeded"
                                        % self.max_bytes )
            app_iter = [payload]

        response = MyResponse(headerlist=headerlist, app_iter=app_iter)

        if cache_bypass:
            response.cache_control = "no-cache"
        else:
            if self.cache_control:
                response.cache_control = self.cache_control

        return response


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
        params = request.environ['rdfrest.parameters']
        with self._service:
            results = resource.post_graph(graph, params or None)
        if not results:
            return MyResponse(status=205, request=request) # Reset
        else:
            content = "\r\n".join( "{}".format(r) for r in results ) + "\r\n"
            headerlist = [
                ("location", str(results[0])),
                ("content-type", "text/uri-list"),
                ]
            return MyResponse(content, status=201, headerlist=headerlist,
                               request=request) # Created

    def http_put(self, request, resource):
        """Process a PUT request on the given resource.

        .. note::

            If `resource` has an `iter_etags` properties, then it is
            required that `request` include an ``If-Match`` header
            field. Note that those etags are *weak* etags (see
            :class:`~rdfrest.cores.mixins.BookkeepingMixin`), which are not
            allowed in ``If-Match`` according to :RFC:`2616`. However,
            this limitation will probably be dropped in future
            versions of HTTP, so do not follow it.
        """
        # too many return statements (7/6) #pylint: disable=R0911

        params = request.environ['rdfrest.parameters']

        # find parser
        ext = request.uri_extension
        if ext:
            parser = None
            _, ctype = get_serializer_by_extension(ext)
            if ctype is not None:
                parser, _ = get_parser_by_content_type(ctype)
            if parser is None:
                return self.issue_error(404, request, resource, "Bad extension")
        else:
            ctype = request.content_type or "text/turtle"
            iter_etags = getattr(resource, "iter_etags", None)
            if iter_etags is not None:
                if request.headers.get("if-match", "*") == "*":
                    return MyResponse(
                        status="403 Forbidden: 'if-match' is required",
                        request=request,
                        )
                for i in iter_etags(params or None):
                    if taint_etag(i, ctype) in request.if_match:
                        break
                else: # no matching etag found in 'for' loop
                    for i in etag_variants(iter_etags(params or None)):
                        if taint_etag(i, ctype) in request.if_match:
                            break
                    else:
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
            with resource.edit(params or None, True) as graph:
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
        :type  resource: rdfrest.cores.local.ILocalCore
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
        if message is not None:
            body = "%s\n%s" % (body, message)

        LOG.debug("HttpFrontend.issue_error - %s\n%s\n%s\n", status, body, "\n".join(traceback.format_stack()))

        body = """%s

Service info
  class name: %s
  root URI  : %s
        """ % (
            body,
            self._service.__class__.__name__,
            self._service.root_uri,
        )
        res = MyResponse(body, status, list(kw.items()))
        return res


def taint_etag(etag, ctype):
    """I taint etag with the given content-type.

    This is required because caches may be smart with different entities of the
    same resources, as described in RFC 2616, sec 13.6.
    """
    return "%s/%s" % (ctype, etag)
    # TODO LATER make a more opaque (unreversible?) tainting operation?

def etag_variants(etags):
    """Some Web server modify etags when they alter the entity.
    This tries function iterates over variants of the given etags,
    to try and match them against a given query.
    """
    for etag in etags:
        yield "%s-gzip" % etag # Apache with gzip encoding

class _TooManyTriples(Exception):
    """This exception class is used to abort edit context during PUT.
    """
    pass

###############################################################
#
# WSGI Middleware registry
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

    In addition to standard WSGI entries,
    the ``environ`` passed to middlewares will include:

    * ``rdfrest.resource``: the requested resource; may be None
    * ``rdfrest.requested.uri``: the URI (as an ``rdflib.URIRef``)
      requested by the client, without its extension (see below)
    * ``rdfrest.requested.extension``: the requested extension; may be ``""``

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
        if pair[1] == middleware:
            del _MIDDLEWARE_REGISTRY[i]
            global _MIDDLEWARE_STACK_VERSION
            _MIDDLEWARE_STACK_VERSION += 1
            return
    if not quiet:
        raise ValueError("pre-processor not registered")


TOP = 0
ERROR_HANDLING = 100
SESSION = 200
AUTHENTICATION = 400
AUTHORIZATION = 600
BOTTOM = 800

###############################################################
#
# Error handling middleware
#

class ErrorHandlerMiddleware(object):
    """
    I intercept a wide range of exceptions, and convert them to HTTP errors.
    """
    #pylint: disable=R0903
    #  too few public methods

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        try:
            return self.app(environ, start_response)

        except HttpException as ex:
            response = ex.get_response(MyRequest(environ))
        except CanNotProceedError as ex:
            status = "409 Conflict"
            response = MyResponse("%s - Can not proceed\n%s"
                                  % (status, ex.args[0]),
                                  status=status,
                                  request=MyRequest(environ))
        except InvalidDataError as ex:
            status = "403 Forbidden"
            response = MyResponse("%s - Invalid data\n%s"
                                  % (status, ex.args[0]),
                                  status=status,
                                  request=MyRequest(environ))
        except InvalidParametersError as ex:
            status = "404 Not Found"
            response = MyResponse("%s - Invalid parameters\n%s"
                                  % (status, ex.args[0]),
                                  status=status,
                                  request=MyRequest(environ))
        except MethodNotAllowedError as ex:
            status = "405 Method Not Allowed"
            response = MyResponse("%s\n%s" % (status, ex.args[0]),
                                  status=status,
                                  request=MyRequest(environ))
            # TODO LATER find a nice way to populate response.allow ?
        except ParseError as ex:
            status = "400 Bad Request"
            response = MyResponse("%s - Parse error\n%s"
                                  % (status, ex.args[0]),
                                  status=status,
                                  request=MyRequest(environ))
        except ParseException as ex:
            status = "400 Bad Request"
            message = "%s at line %s col %s\n\n%s" % \
                      (ex.args[0], ex.lineno, ex.column, ex.markInputline())
            response = MyResponse("%s - Parse exception\n%s"
                                  % (status, message),
                                  status=status,
                                  request=MyRequest(environ))
        except SerializeError as ex:
            status = "550 Serialize Error"
            message = ex.args[0]
            if environ.get('rdfrest.send-traceback'):
                message = "%s\n%s" % (message, traceback.format_exc())
            response = MyResponse("%s\n%s" % (status, message),
                                  status=status,
                                  request=MyRequest(environ))
        except Exception as ex:
            status = "500 Internal Error"
            message = ex.args[0]
            if environ.get('rdfrest.send-traceback'):
                message = "%s\n%s" % (message, traceback.format_exc())
            response = MyResponse("%s - Unexpected exception\n%s"
                                  % (status, message),
                                  status=status,
                                  request=MyRequest(environ))

        return response(environ, start_response)

register_middleware(ERROR_HANDLING, ErrorHandlerMiddleware)

class HttpException(Exception):
    def __init__(self, message, status, **headers):
        super(HttpException, self).__init__(message)
        self.status = status
        self.headers = headers

    def get_body(self):
        return "%s\n%s" % (self.status, self.message)

    def get_headerlist(self):
        hlist = []
        for key, val in self.headers.items():
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

def best_match(accepter, offers):
    """
    Return the best acceptable offer from 'offers' by 'accepter',
    or None if there is no match.
    """
    ao = accepter.acceptable_offers(offers)
    if ao:
        return ao[0][0]
    else:
        None
