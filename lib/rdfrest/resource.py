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
I provide the class `Resource`, the atomic component of an RDF-Rest service.
"""
from rdflib import Graph, RDF, RDFS, URIRef
from webob import Request, Response
from .serializer import serialize, serialize_version_list
from .utils import make_fresh_resource


class Resource(object):
    """
    I provide a framework for implementing `Service` resources.

    :params:
        :sercive: the `Sercive` instance containing this resource
        :uri:     the resource URI (as a URIRef)
    """

    # subclasses must override this attribute; see Service.register
    MAIN_RDF_TYPE = RDFS.Resource # just to please pylint really

    def __init__(self, service, uri):
        assert isinstance(uri, URIRef), repr(uri)
        self.service = service
        self.uri = uri
        store = service.store
        self.graph = Graph(store, uri)
        self.private = Graph(store, URIRef(uri+"#private"))
    
    def __call__(self, environ, start_response):
        """
        Honnor the WSGI interface.

        If this class needs to be wrapped in a WSGI middleware, it is
        compatible with the WSGI interface.
        
        :see-also: `Wsgi2Resource`
        """
        request = Request(environ)
        response = self.get_response(request)
        response(environ, start_response)

    def init(self, new_graph):
        """
        Initialize RDF graphs.

        ``new_graph`` is an RDF graph which is assumed to have passed
        `check_new_graph`.

        This method is called to actually create the resource *in the RDF
        store*. It can be used to automatically generate RDF statements about
        the resource.

        Note that this method is not necessarily called when the *instance* is
        created (if it is recreated from an existing resource in the RDF store)
        so it is *not* a good idea to define instance attributes here.
        """
        for triple in new_graph:
            self.graph.add(triple)
        self.private.add((URIRef(self.uri), RDF.type, self.MAIN_RDF_TYPE))

    def get_response(self, request):
        """
        Dispatch the request to the appropriate http_X method.

        :params:
                   :request: a `webob.Request` object

        :return:   a `webob.Response` object
        :see-also: `http_head`
        """
        method = request.method
        implementation = getattr(self, "http_%s" % method.lower(), None)
        if implementation is None:
            return self.service.method_not_allowed(request)
        else:
            return implementation(request)

    def http_head(self, request):
        """
        Default implementation, using http_get.

        :params:
                   :request: a `webob.Request` object

        :return:   a `webob.Response` object
        :see-also: `get_response`
        """
        http_get = getattr(self, "http_get", None)
        if http_get is None:
            return self.service.method_not_allowed(request)
        else:
            res = http_get(request)
            res.body = None
            return res

    def negociate_rdf_content(self, response, graph):
        """
        Populate ``response`` with the appropriate representation of ``graph``.

        I use the content negociation header fields from ``response.request``,
        and the registered serializers.

        It is assumed that ``response.request`` contains the request.

        Subclasses could override this method to support specialized syntaxes.
        """
        req = response.request
        gen, mimetype, extension = serialize(graph, req, req.extension)
        if gen is None:
            if req.extension:
                # the extension was not recognized
                return Response("Unknown extension", status=404)
            else:
                # no acceptable representation found
                msg, ctype = serialize_version_list(self.uri, req)
                return Response(msg, content_type=ctype, status=406)
                # TODO MINOR should we instead default to RDF/XML ?
                # This is acceptable per RFC 2616 (HTTP 1.1), and is
                # apparently considered better practice

        location = "%s.%s" % (self.uri, extension)
        query_string = req.query_string
        if query_string:
            location = "%s?%s" % (location, query_string)

        response.app_iter = gen
        response.content_type = mimetype
        response.content_location = location

    @classmethod
    def check_new_graph(cls, _request, _uri, _new_graph):
        """
        I check that a graph is a valid representation of this resource class.

        If acceptable, None is returned; else, a Response with the appropriate
        error status should be returned.

        This method may also alter new_graph if required.

        This class method can be overridden by subclasses that have constraints
        on the representation of their instances.

        TODO: describe parameters
        """
        return None

    @classmethod
    def mint_uri(cls, _created, new_graph, target_uri):
        """
        I mint a URI for a resource of that class.

        ``new_graph`` is supposed to be a graph POSTed to ``target_uri``, in
        which ``created`` is a non-URI node representing the resource to be
        created, and that resource must of cours be an instance of ``cls``.

        Return the minted URI.

        The default behaviour is to generate a child URI of target_uri, with
        a trailing slash if this class has an ``http_post`` method.
        """
        assert target_uri[-1] == "/"
        prefix = "%s%s-" % (target_uri, cls.__name__.lower())
        if hasattr(cls, "http_post"):
            suffix = "/"
        else:
            suffix = ""
        return make_fresh_resource(new_graph, prefix, suffix)
        

class Wsgi2Resource(object):
    """
    Wrap an WSGI application into a `Service` resource.
    """
    #pylint: disable=R0903
    #    too few public methods
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def get_response(self, request):
        """
        Implement `Resource` API.
        """
        return request.get_response(self.wsgi_app)

