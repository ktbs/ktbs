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

from rdfrest.exceptions import CorruptedStore
from rdfrest.namespaces import RDFREST

class Service(object):
    """
    An RDF-REST service is a set of `rdfrest.resource.Resource resources`.

    One particular resource, called the *root* of the service, is the entry
    point to the service.

    Actual implementations should subclass this class, then use class methods
    :meth:`register` and :meth:`register_root` to customize their behaviour.
    """

    _class_map = None
    _root_cls = None

    def __init__(self, store, root_uri, create=True):
        """
        Initializes this RdfRest service with the given store.

        :param store:    the RDF store containing the data of this service
        :type  store:    rdflib.store.Store
        :param root_uri: the URI of the root resource of this service
        :type  root_uri: rdflib.URIRef
        :param create:   if `store` is empty, populate it with initial data?
        """
        assert self._class_map, "No registered resource class"
        assert self._root_cls, "No registered root resource class"

        self.store = store
        self.root_uri = root_uri
        self._resource_cache = res_cache = {}
        self._context_level = 0
        if len(store) == 0:
            assert create, "Empty store; `create` should be allowed"
            root_cls = self._root_cls
            graph = root_cls.create_root_graph(root_uri)
            root = root_cls.create(self, self.root_uri, graph)
            res_cache[str(root_uri)] = root
        
    @classmethod
    def register(cls, py_class):
        """Register `py_class` as a resource implementation.

        The given class `py_class` must have an attribute RDF_MAIN_TYPE, which
        is a URIRef.

        This method can be used as a class decorator.
        """
        class_map = cls._class_map
        if class_map is None:
            class_map = cls._class_map = {}

        rdf_type = py_class.RDF_MAIN_TYPE
        assert isinstance(rdf_type, URIRef)
        assert rdf_type not in class_map, "Conflicting implementation"
        class_map[rdf_type] = py_class
        return py_class

    @classmethod
    def register_root(cls, py_class):
        """Register `py_class` as a resource implementation *and* as the
        class of the `root`:attr: resource.

        :see-also: :meth:`register`

        This method can be used as a class decorator.
        """
        assert cls._root_cls is None
        cls.register(py_class)
        cls._root_cls = py_class
        return py_class

    @property
    def root(self):
        """Get the root resource of this service.

        :rtype: rdfrest.resource.Resource
        """
        ret = self.get(self.root_uri)
        if ret is None:
            raise CorruptedStore("root resource not found")
        return ret

    def get(self, uri):
        """Get a resource from this service.

        :param uri: the URI of the resource, stripped from any query-string
        :type  uri: str

        :return: the resource, or None
       
        :see-also: :meth:`register`
        """
        resource = self._resource_cache.get(uri)
        if resource is None:
            private = Graph(self.store, URIRef(uri + "#private"))
            if len(private) == 0:
                return None
            uri = URIRef(uri)
            types = list(private.objects(uri, _HAS_IMPL))
            assert len(types) == 1, types
            py_class = self._class_map.get(types[0])
            assert py_class is not None, "corrupted store"
            resource = py_class(self, uri)
            self._resource_cache[uri] = resource
        return resource

    def __enter__(self):
        """Start to modifiy this service.
        """
        self._context_level += 1

    def __exit__(self, typ, value, traceback):
        """Ends modifications to this service.
        """
        level = self._context_level - 1
        self._context_level = level
        if level == 0:
            if typ is None:
                self.store.commit()
            else:
                self.store.rollback()
        # TODO: decide what to do if self.store does *not* support rollback
        

_HAS_IMPL = RDFREST.hasImplementation
