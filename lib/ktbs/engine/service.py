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

import urlparse

from os import getpid
from rdflib import Graph, RDF, URIRef, Literal

from rdfrest.cores.local import Service
from rdfrest.util import parent_uri
from .builtin_method import get_builtin_method_impl, iter_builtin_method_impl
from .base import Base
from .ktbs_root import KtbsRoot
from .method import Method
from .obsel import Obsel
from .trace import StoredTrace, ComputedTrace
from .trace_model import TraceModel
from .trace_obsels import StoredTraceObsels, ComputedTraceObsels
from ..namespace import KTBS
from ..config import get_ktbs_configuration
from .. import __version__ as ktbs_version
from .. import __commitno__ as ktbs_commit
import ktbs.serpar


# make ktbs:/ URIs use relative, query, fragments
urlparse.uses_fragment.append("ktbs")
urlparse.uses_query.append("ktbs")
urlparse.uses_relative.append("ktbs")
    
def make_ktbs(root_uri=None, repository=None, create=None):
    """I create a kTBS engine conforming with the `abstract-ktbs-api`:ref:.

    :param root_uri:   the URI to use as the root of this kTBS
                       (defaults to <ktbs:/>)
    :param repository: where to store kTBS data
    :param create:     whether the data repository should be initialized;
                       (see below)

    Parameter `repository` can be either a path (in which case data will be
    stored in a directory of that name, which will be created if needed), or a
    string of the form ``":store_type:configuration_string"`` where `store_type`
    is a registered store type in :mod:`rdflib`, and `configuration_string` is
    used to initialize this store.

    If `repository` is omitted or None, a volatile in-memory repository will be
    created.

    If the repository is in-memory or a non-existing path, it will be
    initialized. In all other cases (i.e. existing path or explicit `store_type`),
    the repository is assumed to be already initialized;
    the ``force-init`` option in the ``rdf_database`` section can be
    set to force the initialization in those cases.
    """

    ktbs_config = get_ktbs_configuration()

    if repository is not None:
        ktbs_config.set('rdf_database', 'repository', repository)

    if root_uri is None:
        if repository is None:
            ktbs_config.set('server', 'fixed-root-uri', 'ktbs://{!s}/'.format(getpid()))
        else:
            ktbs_config.set('server', 'fixed-root-uri', 
                            'ktbs://{:s}/'.format(ktbs_config.get('rdf_database', 'repository',1)))
    else:
        ktbs_config.set('server', 'fixed-root-uri', root_uri)

    service = KtbsService(ktbs_config)

    ret = service.get(service.root_uri, _rdf_type=KTBS.KtbsRoot)
    assert isinstance(ret, KtbsRoot)
    return ret


class KtbsService(Service):
    """The KTBS service.
    """

    def __init__(self, service_config=None):
        """I override `Service.__init__` to update the built-in methods.

        :param service_config: kTBS configuration

        root_uri: the URI of this kTBS
        store: the rdflib store containing this kTBS data
        create: whether the store should be initialized with fresh data
        
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

        # self.init_ktbs : always give the initialization method
        Service.__init__(self, classes, service_config, self.init_ktbs)

        root = self.get(URIRef(self.root_uri))

        # testing that all built-in methods are still supported
        for uri in root.state.objects(self.root_uri, KTBS.hasBuiltinMethod):
            if not get_builtin_method_impl(uri):
                raise Exception("No implementation for built-in method <%s>"
                                % uri)
        # updating version number
        with root.edit(_trust=True) as graph:
            graph.set((self.root_uri,
                       KTBS.hasVersion,
                       Literal("%s%s" % (ktbs_version, ktbs_commit))))

    def get(self, uri, _rdf_type=None, _no_spawn=False):
        """I override :meth:`rdfrest.cores.local.Service.get`

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
