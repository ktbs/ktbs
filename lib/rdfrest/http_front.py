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

"""I provide an :class:`HttpFrontend HTTP front-end` for
:class:`rdfrest.service.Service`.
"""
from rdfrest.exceptions import CanNotProceedError, InvalidDataError, \
    InvalidParametersError, MethodNotAllowedError, ParseError, \
    RdfRestException, Redirect, SerializeError
from rdfrest.parser import ParserRegister
from rdfrest.response import MyResponse
from rdfrest.serializer import SerializerRegister
from rdfrest.utils import extsplit

from datetime import datetime
from webob import Request
from webob.response import status_reasons

class HttpFrontend(object):
    """The role of the HTTP front-end is to relay requests to and response
    from the service through the HTTP protocol. This involves parsing and
    serializing different content-types to and from RDF graphs.
    
    The class HttpFrontend comes with a number of generic parsers and
    serializers, but a registration mechanism allows to extend it with
    support for additional content-types, either generic or
    resource-specific.
    
    In the future, HttpFrontend may also include on-the-fly translation of
    contents, for changing internal URIs into URIs served by the
    HttpFrontend.

    :param service: the service to expose over HTTP

    Additionally, the following keyword arguments are recognized:

    :param serializers:   a serializer register (if None, the default one will
                          be used)
    :type  serializers:   serializer.SerializerRegister
    :param parsers:       a parser register (if None, the default one will be
                          used)
    :type  parsers:       parser.ParserRegister
    :param) options:      additional informations
    :type  options: dict
    :param cache_control: a callable accepting a Resource and returning either
                          None or the value of the cache-control header field.

    .. warning::
    
        RDF-REST is meant to differenciate an empty query-string from no
        query-string at all (see `parameters definition
        <rdfrest-parameters>`:ref:). However, WSGI does not allow such a
        distinction. This implementation therefore assumes that an empty
        query-string is no query-string at all.

    """

    def __init__(self, service, **options):
        """See class docstring.
        """
        # __init__ not called in mixin #pylint: disable=W0231
        # NB: strange, pylint should recognized it is a mixin...
        self._service = service
        self.serializers = options.pop("serializers", None) \
                           or SerializerRegister.get_default()
        self.parsers = options.pop("parsers", None) \
                       or ParserRegister.get_default()
        self.cache_control = options.pop("cache_control", None) \
                             or (lambda *a: None)
        self._options = options or {}

    def __call__(self, environ, start_response):
        """Wrap `get_response` to honnor the WSGI protocol.
        """
        request = Request(environ)
        response = self.get_response(request)
        return response(environ, start_response)
        
    def get_response(self, request):
        """Process a webob request and return a webob response.

        :param request: a webob Request
        """
        resource_uri, request.uri_extension = extsplit(request.path_url)
        resource = self._service.get(resource_uri)
        if resource is None:
            return self.issue_error(404, request, None)
        method = getattr(self, "http_%s" % request.method.lower(), None)
        if method is None:
            return self.issue_error(405, request, resource)
        try:
            response = method(request, resource)
        except CanNotProceedError, ex:
            response = MyResponse(ex.message,
                                  status="409 Conflict",
                                  request=request)
        except InvalidDataError, ex:
            response = MyResponse(ex.message,
                                  status="403 Forbidden",
                                  request=request)
        except InvalidParametersError, ex:
            response = MyResponse(ex.message,
                                  status="404 Not Found",
                                  request=request)
        except MethodNotAllowedError, ex:
            response = MyResponse(ex.message,
                                  status="405 Method Not Allowed",
                                  request=request)
            response.allow = " ".join(ex.allowed)
        except ParseError, ex:
            response = MyResponse(ex.message,
                                  status="400 Bad Request: Parse error",
                                  request=request)
        except Redirect, ex:
            response = MyResponse(ex.message, status="303 See Other",
                                  request=request)
            response.location = str(ex.uri)
        except SerializeError, ex:
            response = MyResponse(ex.message, status="550 Serialize Error",
                                   request=request)
        except RdfRestException, ex:
            response = MyResponse(ex.message, status=400, request=request)

        except Exception, ex:
            self._service.store.rollback()
            raise

        if response.status[0] == "2":
            # NB: we commit even if the request was a GET, because it may
            # have modified the '#private' graphs
            self._service.store.commit()
        else:
            self._service.store.rollback()

        cache_control = self.cache_control(resource)
        if cache_control is not None:
            response.cache_control = cache_control
            
        return response

    def http_delete(self, request, resource):
        """Process a DELETE request on the given resource.
        """
        # method could be a function #pylint: disable=R0201
        # TODO how can we transmit context (authorization? anything else?)
        resource.rdf_delete(request.queryvars.mixed() or None)
        return MyResponse(status="204 Resource deleted", request=request)

    def http_get(self, request, resource):
        """Process a GET request on the given resource.
        """
        ext = request.uri_extension
        if ext:
            serializer, ctype = self.serializers.get_by_extension(ext)
            if serializer is None:
                return self.issue_error(404, request, resource)
        else:
            serializer = None
            ctype = request.accept.best_match( ser[1]
                                               for ser in self.serializers )
            if ctype is None:
                # 406 Not Acceptable
                version_list = [ "<%s.%s>  (%s)" % (resource.uri, i[2], i[1])
                                 for i in self.serializers if i[2] ]
                return MyResponse("\n".join(version_list),
                                  status="406 Not Acceptable",
                                  request=request)
            # else we can be certain that the serializer exists, so:
            serializer, ext = self.serializers.get_by_content_type(ctype)

        headerlist = []
        headerlist.append(("content-type", ctype))
        if ext is not None:
            headerlist.append(("content-location",
                               str("%s.%s" % (resource.uri, ext))))
        etag = getattr(resource, "etag", None)
        if etag is not None:
            headerlist.append(("etag", 'W/"%s"' % etag))
        last_modified = getattr(resource, "last_modified", None)
        if last_modified is not None:
            last_modified = datetime.fromtimestamp(last_modified).isoformat()
            headerlist.append(("last-modified", last_modified))
        try:
            graph = resource.rdf_get(request.queryvars.mixed() or None)
            app_iter = serializer(
                graph,
                self.serializers,
                resource.uri)
        except SerializeError, ex:
            return MyResponse(ex.message, status="550 Serialize error")
            # TODO MINOR may be iter over other serializers?

        #return MyResponse(headerlist=headerlist, app_iter=app_iter)
        res = MyResponse(headerlist=headerlist, app_iter=app_iter)
        return res

    def http_head(self, request, resource):
        """Process a HEAD request on the given resource.
        """
        response = self.http_get(request, resource)
        return MyResponse(status=response.status,
                           headerlist=response.headerlist, request=request)

    def http_post(self, request, resource):
        """Process a GET request on the given resource.
        """
        parser = self.parsers.get_by_content_type(request.content_type
                                                   or "text/turtle")
        if parser is None:
            return self.issue_error(415, request, resource)
        graph = parser(request.body, resource.uri, request.charset)
        results = resource.rdf_post(graph, request.queryvars.mixed() or None)
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

            If `resource` has an `etags` properties, then it is
            required that `request` include an ``If-Match`` header
            field. Note that those etags are *weak* etags (see
            :class:`~rdfrest.mixins.BookkeepingMixin`), which are not
            allowed in ``If-Match`` according to :RFC:`2616`. However,
            this limitation will probably be dropped in future
            versions of HTTP, so do not follow it.
        """
        etag = getattr(resource, "etag", None)
        if etag is not None:
            if request.headers.get("if-match", "*") == "*":
                return MyResponse(
                    status="403 Forbidden: 'if-match' is required",
                    request=request,
                    )
            if not etag in request.if_match:
                return self.issue_error(412, request, resource)

        parser = self.parsers.get_by_content_type(request.content_type
                                                   or "text/turtle")
        if parser is None:
            return self.issue_error(415, request, resource)
        graph = parser(request.body, resource.uri, request.charset)
        resource.rdf_put(graph, request.queryvars.mixed() or None)
        return self.http_get(request, resource)

    def issue_error(self, status, request, resource):
        """Issues an HTTP error.

        :param status:   the HTTP status
        :type  status:   int
        :param request:  the request being processed
        :type  request:  webob.Request
        :param resource: the resource being addressed (can be None)
        :type  resource: rdfrest.resource.Resource

        Can be overridden by subclasses to provide custom error messages.
        """
        # this method is intended to be overridden, so the following pylint
        # errors are not relevant:
        # * method could be a function #pylint: disable=R0201 
        # * unsued argument            #pylint: disable=W0613

        status = "%s %s" % (status, status_reasons[status])
        res = MyResponse("RDF-REST error: %s\n" % status, status=status)
        if status[:3] == "405":
            res.allow = "HEAD, GET, PUT, POST, DELETE"
        return res
