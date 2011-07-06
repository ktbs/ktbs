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
I provide the class `Service`, the entry point to an RDF-Rest service.
"""
from rdflib import Graph, RDF, URIRef
from webob import Request, Response

from .utils import extsplit


class Service(object):
    """
    An RDF-rest service is a set of `rdfrest.resource.Resource resources`.

    I dispatch HTTP requests to the appropriate resource. The python class
    implementing a resource is determined by its RDF type. A python class is
    attached to an RDF type for a given subclass of `Service` by decorating
    that python class with the `Service.register` class method.
    """

    def __init__(self, config):
        """
        Initializes this RdfRest service with the given configuration.

        :params:
            :config: a dict containing configuration options (see below)

        :configuration options:
            :rdfrest.store: a context-aware RDF store (required)
            :rdfrest.base:  the base URI of the service (required)
        """
        self.store = config["rdfrest.store"]
        self.base = config["rdfrest.base"]
        
        self._resource_cache = {}

        self.update_layout()

        
    def update_layout(self):
        """
        Check whether the layout of the RDF respository is consistent with
        this implementation, and update it if possible.
        """
        pass


    def __call__(self, environ, start_response):
        """
        Dispatch request to the appropriate `Resource`.
        """
        req = Request(environ)
        req.resource_uri, req.extension = extsplit(req.path_url)

        resource = self.get_resource(req)
        if resource:
            res = resource.get_response(req)
            res = self.postprocess_response(res)
        else:
            res = self.not_found(req)
        return res(environ, start_response)


    @classmethod
    def register(cls, py_class):
        """
        Register `py_class` as a resource implementation.

        The given class `py_class` must have an attribute MAIN_RDF_TYPE, which
        is a URIRef. This 

        This method can be used as a class decorator.
        """
        class_map = getattr(cls, "class_map", None)
        if class_map is None:
            class_map = cls.class_map = {}

        rdf_type = py_class.MAIN_RDF_TYPE
        assert isinstance(rdf_type, URIRef)
        assert rdf_type not in class_map, "Conflicting implementation"
        class_map[rdf_type] = py_class
        return py_class

            
    def get_resource(self, request):
        """
        Return the `Resource` that will handle the request, or None.

        This method may also alter the request to suit the need of the
        resource.
       
        :see-also: `register`
        :see-also: `Wsgi2Resource`
        """
        uri = request.resource_uri
        resource = self._resource_cache.get(uri)
        if resource is None:
            assert hasattr(self, "class_map"), "No resource class declared"
            
            private = Graph(self.store, URIRef(uri + "#private"))
            if len(private) == 0:
                return None
            uri = URIRef(uri)
            types = list(private.objects(uri, RDF.type))
            if len(types) != 1:
                raise Exception("Resource should have exactly 1 type, "
                                "found %s (%s)" % (len(types),
                                                   ",".join(str(t)
                                                            for t in types)))
            py_class = self.class_map.get(types[0])
            resource = py_class(self, uri)
            self._resource_cache[uri] = resource
        return resource

        
    def postprocess_response(self, response):
        """
        Post-process the response returned by a resource.

        :see-also: `get_resource`
        """
        #pylint: disable=R0201
        #    method could be a function (it is intended to be overridden) 

        return response


    def not_found(self, request):
        """
        Issues a 404 (resource not found) response.
        """
        #pylint: disable=R0201,W0613
        #    method could be a function (it is intended to be overridden) 
        #    unused argument 'request'

        res = Response("resource not found", status=404)
        return res


    def method_not_allowed(self, request):
        """
        Issues a 405 (method not allowed) response.
        """
        #pylint: disable=R0201
        #    method could be a function (it is intended to be overridden) 

        res = Response("method not allowed: %s" % request.method, status=405)
        return res


# TODO MAJOR implement locking mechanism
# if either env["wsgi.multithread"] or env["wsgi.multiprocess"] is set
