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
from rdflib import Graph, URIRef

from rdfrest.namespaces import RDFREST

class Service(object):
    """
    An RDF-rest service is a set of `rdfrest.resource.Resource resources`.

    I dispatch HTTP requests to the appropriate resource. The python class
    implementing a resource is determined by its RDF type. A python class is
    attached to an RDF type for a given subclass of `Service` by decorating
    that python class with the `Service.register` class method.
    """

    def __init__(self, store):
        """
        Initializes this RdfRest service with the given store.
        
        :type store: rdflib.store.Store
        """
        self.store = store
        self._resource_cache = {}
        
    @classmethod
    def register(cls, py_class):
        """Register `py_class` as a resource implementation.

        The given class `py_class` must have an attribute MAIN_RDF_TYPE, which
        is a URIRef.

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
            
    def get(self, uri):
        """Get a resource from this service.

        :param uri: the URI of the resource, stripped from any query-string
        :type  uri: str

        :return: the resource, or None
       
        :see-also: `register`
        """
        resource = self._resource_cache.get(uri)
        if resource is None:
            assert hasattr(self, "class_map"), "No resource class declared"
            
            private = Graph(self.store, URIRef(uri + "#private"))
            if len(private) == 0:
                return None
            uri = URIRef(uri)
            types = list(private.objects(uri, _HAS_IMPL))
            assert len(types) == 1, types
            py_class = self.class_map.get(types[0])
            resource = py_class(self, uri)
            self._resource_cache[uri] = resource
        return resource

    # TODO MAJOR ensures underlying store supports transactions; if not, they
    # should perhaps be emulated

    def commit(self):
        """Commit pending modifications.
        """
        self.store.commit()

    def rollback(self):
        """Rollback pending modifications.
        """
        self.store.rollback()
        

_HAS_IMPL = RDFREST.hasImplementation
