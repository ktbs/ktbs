#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    KTBS is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    KTBS is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with KTBS.  If not, see <http://www.gnu.org/licenses/>.
"""
I implement KTBS as an `rdfrest.service.Service`:class.
"""
from rdflib import Graph, URIRef
from rdfrest.namespaces import RDFREST
from rdfrest.service import Service

from ktbs.namespaces import KTBS

class KtbsService(Service):
    """The KTBS service.
    """

    def __init__(self, store, root_uri, create=True):
        """I override ``Service.__init__`` to update the built-in methods.
        
        NB: built-in methods may change from one execution to another, so
        they have to be updated in the store at each execution.
        """
        Service.__init__(self, store, root_uri, create=True)
        root_uri = URIRef(root_uri)
        bims = set(URIRef(bim) for bim in self._BUILTIN_METHODS)
        root_graph = Graph(store, root_uri)
        for bim in root_graph.objects(root_uri, _HAS_BUILTIN_METHOD):
            if bim not in bims:
                root_graph.remove((root_uri, _HAS_BUILTIN_METHOD, bim))
                private = Graph(store, URIRef(bim+"#private"))
                private.remove((None, None, None))
            else:
                bims.remove(bim)
        for bim in bims:
            root_graph.add((root_uri, _HAS_BUILTIN_METHOD, bim))
            private = Graph(store, URIRef(bim+"#private"))
            private.add((bim, _HAS_IMPL, _BUILTIN_METHOD))
            
    
    @classmethod
    def iter_builtin_method_uris(cls):
        """I return an iterable of all supported built-in methods.
        """
        for i in cls._BUILTIN_METHODS:
            yield i

    @classmethod
    def register_builtin_method(cls, implementation):
        """I register the implementation of a builtin method.
        """
        uri = str(implementation.uri)
        cls._BUILTIN_METHODS[uri] = implementation

    @classmethod
    def has_builtin_method(cls, uri):
        """I return True if uri is recognized as a built-in method.
        """
        return str(uri) in cls._BUILTIN_METHODS
        
    def get(self, uri):
        """Override `Service.get` to dynamically check built-in methods
        (as built-in methods may appear or disappear between executions).
        """
        ret = super(KtbsService, self).get(uri)
        if ret is None:
            if uri in self._BUILTIN_METHODS:
                ret = uri
        return ret

    _BUILTIN_METHODS = {}

class BuiltinMethod(object):
    """Dummy class used for instantiating built-in methods.
    """
    # too few public method #pylint: disable=R0903
    RDF_MAIN_TYPE = KTBS.BuiltinMethod
    def __init__(self, service, uri):
        self.service = service
        self.uri = uri

# registering all resources classes
from ktbs.local.root import KtbsRoot
from ktbs.local.base import Base
from ktbs.local.model import Model
from ktbs.local.method import Method
from ktbs.local.trace import StoredTrace

KtbsService.register_root(KtbsRoot)
KtbsService.register(Base)
KtbsService.register(Model)
KtbsService.register(Method)
KtbsService.register(BuiltinMethod)
KtbsService.register(StoredTrace)

# registering default builtin methods
from ktbs.methods.filter import FILTER
from ktbs.methods.fusion import FUSION
from ktbs.methods.sparql import SPARQL
from ktbs.methods.parallel import PARALLEL
from ktbs.methods.external import EXTERNAL

KtbsService.register_builtin_method(FILTER)
KtbsService.register_builtin_method(FUSION)
KtbsService.register_builtin_method(SPARQL)
KtbsService.register_builtin_method(PARALLEL)
KtbsService.register_builtin_method(EXTERNAL)

_BUILTIN_METHOD = KTBS.BuiltinMethod
_HAS_BUILTIN_METHOD = KTBS.hasBuiltinMethod
_HAS_IMPL = RDFREST.hasImplementation
