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
I provide the class `Service`:class:, which provides a set of related
`resources <rdfrest.resource.Resource>`:class:. One particular resource,
called the `~Service.root`:attr: of the service, is its entry point.

Every resource is identified by a URI and backed by an RDF graph (though
subclasses of `~rdfrest.resource.Resource`:class: may completely hide
this). Any resource from the service can be retrieved by passing the resource
URI to the `Service.get`:meth:.

**Modifying the underlying data.**
A `Service`:class provides the python-context interface (*a.k.a.*
``with`` statement). Its direct use will rarely (if ever) be required
(see below), but it deserves some explaination, at least for
implementers of :class:`~rdfrest.resource.Resource` and subclasses.

The role of using a service as a context is to ensure that data is
correctly handled by the underlying RDF store:

    * on normal exit, the changes will be commited to store;

    * if an exception is raised, the changes will be rolled-back from
      the store;

    * if several contexts are embeded (e.g. by calling a function that
      itself uses the service context), the commit/rollback will only
      occur when exiting the *outermost* context;

All methods of :class:`~rdfrest.resource.Resource` modifying the data will
normally takes care of this, and the "outermost context" rule above ensures
that data will only be commited when a *globally* consistent state is reached.

.. warning::

    For the moment (2011-07), rdfrest uses implementation of RDF store
    that do *not* support rollback. This means that the store may end up
    in an inconsistent state whenever an exception occurs while editing a
    resource.

"""
from rdflib import Graph, URIRef

from rdfrest.exceptions import CorruptedStore
from rdfrest.namespaces import RDFREST

class Service(object):
    """

        :param store:    the RDF store containing the data of this service
        :type  store:    rdflib.store.Store
        :param root_uri: the URI of the root resource of this service
        :type  root_uri: rdflib.URIRef
        :param create:   if `store` is empty, populate it with initial data?

    This class should never be used directly, but is meant to be subclassed:

    **To subclass implementers:** Your only job in subclassing
    :class:`Service` will generally be to use class methods
    :meth:`register` and :meth:`register_root` to customize their
    behaviour.

    """

    _class_map = None
    _root_cls = None

    def __init__(self, store, root_uri, create=True):
        """
        Initializes this RdfRest service with the given store.
        """
        assert self._class_map, "No registered resource class"
        assert self._root_cls, "No registered root resource class"

        self.store = store
        self.root_uri = root_uri
        self._resource_cache = {}
        self._context_level = 0
        if len(store) == 0:
            assert create, "Empty store; `create` should be allowed"
            root_cls = self._root_cls
            graph = root_cls.create_root_graph(root_uri)
            root = root_cls.create(self, self.root_uri, graph)
            self._resource_cache[root_uri.defrag()] = root
        
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

        The class method `rdfrest.resource.Resource.create_root_graph`:meth:
        of `py_class` will be used at the service creation to populate the
        store.

        This method can be used as a class decorator.
        """
        assert cls._root_cls is None
        cls.register(py_class)
        cls._root_cls = py_class
        return py_class

    @property
    def root(self):
        """The root resource of this service.

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
        resource = self._resource_cache.get(str(uri))
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
            self._resource_cache[str(uri)] = resource
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
