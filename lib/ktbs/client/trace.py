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
I provide the client implementation of StoredTrace and ComputedTrace.
"""
#pylint: disable-msg=R0904
#    too many public methods
from ktbs.client.resource import Resource, RESOURCE_MAKER
from ktbs.common.computed_trace import ComputedTraceMixin
from ktbs.common.trace import StoredTraceMixin
from ktbs.common.utils import extend_api
from ktbs.namespaces import KTBS

from rdflib import Graph
from rdfrest.client import ProxyStore

@extend_api
class Trace(Resource):
    """TODO docstring
    """

    def __init__(self, uri, graph=None):
        """
        """
        Resource.__init__(self, uri, graph)
        obsels_uri = next(self.graph.objects(self.uri, _HAS_OBSEL_COLLECTION))
        self._obsels = Graph(ProxyStore({"uri":obsels_uri}),
                            identifier=obsels_uri)


    def iter_obsels(self, begin=None, end=None, reverse=False):
        """
        Iter over the obsels of this trace.

        The obsel are sorted by their end timestamp, then their begin
        timestamp, then their identifier. If reverse is true, the order is
        inversed.

        If given, begin and/or end are interpreted as the (included)
        boundaries of an interval; only obsels entirely contained in this
        interval will be yielded.

        * begin: an int, datetime or Obsel
        * end: an int, datetime or Obsel
        * reverse: an object with a truth value

        NB: the order of "recent" obsels may vary even if the trace is not
        amended, since collectors are not bound to respect the order in begin
        timestamps and identifiers.
        """
        if begin or end or reverse:
            raise NotImplementedError(
                "iter_obsels parameters not implemented yet")
            # TODO MAJOR implement parameters of iter_obsels
        make_resource = self.make_resource
        for obs in self._obsels.subjects(_HAS_TRACE, self.uri):
            yield make_resource(obs, _OBSEL)

    

class StoredTrace(StoredTraceMixin, Trace):
    """TODO docstring"""
    # TODO implement client-specifid methods

class ComputedTrace(ComputedTraceMixin, Trace):
    """TODO docstring"""
    # TODO implement client-specifid methods

RESOURCE_MAKER[KTBS.StoredTrace] = StoredTrace
RESOURCE_MAKER[KTBS.ComputedTrace] = ComputedTrace

_HAS_OBSEL_COLLECTION = KTBS.hasObselCollection
_HAS_TRACE = KTBS.hasTrace
_OBSEL = KTBS.Obsel

# the following import ensures that Obsel are registered in RESOURCE_MAKER
import ktbs.client.obsel #pylint: disable-msg=W0611
# NB: we have to disable pylint W0611 (Unused import)
