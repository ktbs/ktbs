#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
I implement :class:`.interface.ICore` as a resource "hosted" by another one.
"""
from functools import wraps
from rdflib import RDF, URIRef

from ..exceptions import MethodNotAllowedError
from ..cores import ICore
from ..wrappers import get_wrapped
from ..util import coerce_to_uri, urisplit

class HostedCore(ICore):
    """A RESTful resource whose description is embeded in another resource.

    This is typically used for resources with a fragment-id in their URI,
    but also for non-informational resource using 303-redirect.

    :param host_resource:  the host resource
    :type  host_resource:  :class:`.interface.ICore`
    :param uri:            this resource's URI (may be relative to host's)
    :type  uri:            basestring
    :param forward_params: whether parameters should be forwarded to host (see
                           below)
    :type  forward_params: bool

    Argument `forward_params` defaults to True (which makes sense for
    fragment-id hosted resource) but may be disabled (which makes sense for
    303-redirect hosted resource).

    .. attribute:: uri

        I implement :attr:`.interface.ICore.uri`.

        I hold this resource's URI as defined at `__init__` time.
    """

    def __init__(self, host_resource, uri, forward_params=True):
        # not calling parents __init__ #pylint: disable=W0231

        assert isinstance(host_resource, ICore)
        self.host = host_resource
        self.uri = coerce_to_uri(uri, host_resource.uri)
        self.forward_params = forward_params

    def __str__(self):
        return "<%s>" % self.uri

    def factory(self, uri, _rdf_type=None, _no_spawn=False):
        """I implement :meth:`.interface.ICore.factory`.

        I simply rely on my host's factory.
        """
        return self.host.factory(uri, _rdf_type, _no_spawn)

    def get_state(self, parameters=None):
        """I implement :meth:`.interface.ICore.get_state`.

        I simply return my host's state.
        """
        if not self.forward_params:
            parameters = None
        return self.host.get_state(parameters)

    def force_state_refresh(self, parameters=None):
        """I implement `interface.ICore.force_state_refresh`.

        I simply force a state refresh on my host.
        """
        if not self.forward_params:
            parameters = None
        self.host.force_state_refresh(parameters)

    def edit(self, parameters=None, clear=False, _trust=False):
        """I implement :meth:`.interface.ICore.edit`.

        I simply return my host's edit context.
        """
        if not self.forward_params:
            parameters = None
        return self.host.edit(parameters, clear, _trust)

    def post_graph(self, graph, parameters=None,
                   _trust=False, _created=None, _rdf_type=None):
        """I implement :meth:`.interface.ICore.post_graph`.

        No data can be posted to a hosted resource; it should be posted to the
        host resource instead.
        """
        # unused arguments #pylint: disable=W0613
        raise MethodNotAllowedError("Can not post to hosted resource <%s>"
                                    % self.uri)

    def delete(self, parameters=None, _trust=False):
        """I implement :meth:`.interface.ICore.delete`.

        A hosted resource can not be deleted. The host resource should be
        altered instead.
        """
        # unused arguments #pylint: disable=W0613
        raise MethodNotAllowedError("Can not delete hosted resource <%s>"
                                    % self.uri)


    ################################################################
    #
    # Other public method spefific to this implementation
    #

    def __eq__(self, other):
        """Two instances with the same URI are considered equal
        """
        return (isinstance(other, HostedCore) and other.uri == self.uri)

    def __hash__(self):
        """Two instances with the same URI will have the same hash
        """
        return hash(HostedCore) ^ hash(self.uri)
        
    @classmethod
    def handle_fragments(cls, factory):
        """I decorate a resource factory to have it handle URIs with frag-id.

        If the URI passed to the factory contains a fragment ID, I will try
        to use the decorated factory to make the host (fragment-less) resource,
        and return the corresponding hosted resource.

        Else, I will pass the URI through to the decorated factory.
        """
        @wraps(factory)
        def decorated_factory(self_or_cls, uri, _rdf_type=None,
                              _no_spawn=False):
            """I wrap a resource factory to handle URIs with frag-id."""
            fragid = urisplit(uri)[4]
            if fragid is None:
                return factory(self_or_cls, uri, _rdf_type, _no_spawn)
            else:
                uri = URIRef(uri)
                host = factory(self_or_cls, URIRef(uri[:-len(fragid)-1]), None,
                               _no_spawn)
                if host is not None:
                    types = host.get_state().objects(uri, RDF.type)
                    py_class = get_wrapped(cls, types)
                    return py_class(host, uri)
                else:
                    return None
            
        return decorated_factory
