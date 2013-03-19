#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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

"""I provide an entry point to create a local kTBS.
"""

from os.path import exists
from rdflib import Graph, plugin as rdflib_plugin, RDF, URIRef
from rdflib.store import Store
from rdfrest.local import Service
from rdfrest.utils import parent_uri
import urlparse

from .builtin_method import get_builtin_method_impl, iter_builtin_method_impl
from .base import Base
from .ktbs_root import KtbsRoot
from .method import Method
from .obsel import Obsel
from .trace import StoredTrace, ComputedTrace
from .trace_model import TraceModel
from .trace_obsels import StoredTraceObsels, ComputedTraceObsels
from ..namespace import KTBS

# make ktbs:/ URIs use relative, query, fragments
urlparse.uses_fragment.append("ktbs")
urlparse.uses_query.append("ktbs")
urlparse.uses_relative.append("ktbs")
    
def make_ktbs(root_uri="ktbs:/", repository=None, create=None):
    """I create a kTBS engine conforming with the `abstract-ktbs-api`:ref:.

    :param root_uri:    the URI to use as the root of this kTBS
                        (defaults to <ktbs:/>)
    :param repository:  where to store kTBS data
    :param create:      whether the data repository should be initialized;
                        (see below)

    Parameter `repository` can be either a path (in which case data will be
    stored in a directory of that name, which will be created if needed), or a
    string of the form ``":store_type:configuration_string"`` where `store_type`
    is a registered store type in :mod:`rdflib`, and `configuration_string` is
    used to initialize this store.

    If `repository` is omitted or None, a volatile in-memory repository will be
    created.

    Parameter `create` defaults to True if `repository` is None or if it is an
    non-existing path; in other cases, it defaults to False.
    """
    if repository is None:
        if create is None:
            create = True
        repository = ":IOMemory:"
    elif repository[0] != ":":
        if create is None:
            create = not exists(repository)
        repository = ":Sleepycat:%s" % repository
    _, store_type, config_str = repository.split(":", 2)
    store = rdflib_plugin.get(store_type, Store)(config_str)
    service = KtbsService(root_uri, store, create)
    ret = service.get(service.root_uri, _rdf_type=KTBS.KtbsRoot)
    assert isinstance(ret, KtbsRoot)
    return ret


class KtbsService(Service):
    """The KTBS service.
    """

    def __init__(self, root_uri, store, create=False):
        """I override `Service.__init__` to update the built-in methods.

        :param root_uri: the URI of this kTBS
        :param store: the rdflib store containing this kTBS data
        :param create: whether the store should be initialized with fresh data
        
        NB: built-in methods may change from one execution to another, so
        they have to be checked against the store.
        """
        classes = [ Base,
                    ComputedTrace,
                    ComputedTraceObsels,
                    KtbsRoot,
                    Method,
                    StoredTrace,
                    StoredTraceObsels,
                    TraceModel,
                    ]
        init_with = create and self.init_ktbs

        Service.__init__(self, root_uri, store, classes, init_with)

        # testing that all built-in methods are still supported
        graph = Graph(self.store, self.root_uri)
        for uri in graph.objects(self.root_uri, KTBS.hasBuiltinMethod):
            if not get_builtin_method_impl(uri):
                raise Exception("No implementation for built-in method <%s>"
                                % uri)

    def get(self, uri, _rdf_type=None, _no_spawn=False):
        """I override :meth:`rdfrest.local.Service.get`

        If the original implementation returns None, I try to make an Obsel.
        """
        ret = super(KtbsService, self).get(uri, _rdf_type, _no_spawn)
        if ret is None:
            parent = super(KtbsService, self).get(URIRef(parent_uri(uri)), None,
                                                  _no_spawn)
            if parent is not None \
            and parent.RDF_MAIN_TYPE in (KTBS.StoredTrace, KTBS.ComputedTrace):
                assert _rdf_type is None or _rdf_type == KTBS.Obsel, _rdf_type
                ret = Obsel(parent, uri)
        return ret
            
    @classmethod
    def init_ktbs(cls, service):
        """I populate the root resource's graph of a new service.
        """
        root_uri = service.root_uri
        graph = Graph(identifier=root_uri)
        graph.add((root_uri, RDF.type, KTBS.KtbsRoot))
        for bim in iter_builtin_method_impl():
            graph.add((root_uri, KTBS.hasBuiltinMethod, bim.uri))
        KtbsRoot.create(service, root_uri, graph)

# unused import #pylint: disable=W0611
# ensures registration of parsers/serializers 
import ktbs.engine.serpar
