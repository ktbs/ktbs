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
I provide the common subclass for all client resources.

I also provide the RESOURCE_MAKER dict where subclasses can register themselves
with a given RDF type; :meth:`Resource.make_resource` relies on it.
"""
from contextlib import contextmanager
from httplib2 import Http
from rdflib import Graph, RDF
from rdflib.graph import ReadOnlyGraphAggregate
from rdfrest.client import ProxyStore

from ktbs.common.resource import ResourceMixin
from ktbs.common.utils import extend_api
from rdfrest.utils import coerce_to_uri

RESOURCE_MAKER = {}

@extend_api
class Resource(ResourceMixin):
    """I am the common subclass for all client resources.

    I honnor all requirements of the the mixin classes provided by
    :mod:`ktbs.common`.

    Resources can also be used as python-contexts (i.e. with the ``with``
    statement) when one wants to perform several modifications before
    actually sending (PUT) data to the distant resource. For example::

        with trace:
            trace.model = other_model
            trace.origin = other_origin
            trace.label = trace.label + " (updated)"

    """
    # just to please pylint, who does not recognize @extend_api ;)
    uri = None
    graph = None

    def __init__(self, uri, graph=None):
        """Initialize Resource common subclass.

        :param uri: Absolute or relative URI.
        :param graph: If no graph is given, it is build from the serialization 
        retrived for this uri.
        """
        #pylint: disable-msg=W0231
        # (not calling __init__ for mixin)
        self.uri = coerce_to_uri(uri)
        if graph is None:
            graph = Graph(ProxyStore({"uri":uri}), identifier=uri)
            graph.open(uri)
        self.__graph = graph
        self._graph = ReadOnlyGraphAggregate([graph])
        # NB: self._graph is made read-only in order to catch implementation
        # errors that would forget to make use of the _edit context
        self._edit_level = 0

    def __eq__(self, other):
        """I am equal to any other `Resource` with the same URI.
        """
        return isinstance(other, Resource) and other.uri == self.uri

    def __hash__(self):
        """The hash of a `Resource` is only determined by its URI.
        """
        return hash(Resource) ^ hash(self.uri)

    def __enter__(self):
        level = self._edit_level
        self._edit_level = level + 1            

    def __exit__(self, typ, value, traceback):
        self._edit_level = level = self._edit_level - 1
        if level == 0:
            if typ is None:
                self.__graph.commit()
            else:
                self.__graph.rollback()

    @property
    @contextmanager
    def _edit(self):
        """I implement the _edit context."""
        with self:
            yield self.__graph

    @staticmethod
    def make_resource(uri, typ=None, graph=None):
        """TODO docstring
        """
        if typ is None:
            if graph is None:
                graph = Graph(ProxyStore({"uri":uri}), identifier=uri)
                graph.open(uri)
            typ = graph.value(uri, _RDF_TYPE)
        maker = RESOURCE_MAKER[typ]
        return maker(uri, graph)

    def remove(self):
        """TODO docstring
        """
        rheader, _rcontent = Http().request(self.uri, 'DELETE')
        if int(rheader.status) / 100 != 2:
            raise ValueError(rheader)
        # TODO improve exception here

    def get_readonly(self):
        """TODO docstring
        """
        return self and False #used self to lure pylint
        # TODO find a good way to know if this resource is readonly

_RDF_TYPE = RDF.type
                
