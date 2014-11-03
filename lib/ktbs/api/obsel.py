# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
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
I provide the pythonic interface ktbs:Obsel .
"""
from rdflib import Literal, RDF
from rdfrest.exceptions import InvalidParametersError, MethodNotAllowedError
from rdfrest.cores import ICore
from rdfrest.util import coerce_to_uri, ReadOnlyGraph
from rdfrest.wrappers import register_wrapper

from .resource import KtbsResourceMixin
from ..namespace import KTBS
from ..utils import extend_api
from ..time import lit2datetime #pylint: disable=E0611

@register_wrapper(KTBS.Obsel)
@extend_api
class ObselMixin(KtbsResourceMixin):
    """
    I provide the pythonic interface of ktbs:Obsel .
    """

    def __eq__(self, other):
        """Guarantees that ObselProxy (below) instances will be equal to
        other implementations.
        """
        return isinstance(other, ObselMixin) and other.uri == self.uri

    def __hash__(self):
        return hash(ObselMixin) ^ hash(self.uri)

    ######## Abstract kTBS API ########

    def get_trace(self):
        """
        I return the trace containing this obsel.
        """
        return self.factory(self.state.value(self.uri, KTBS.hasTrace))
        # must be a .trace.AbstractTraceMixin

    def get_obsel_type(self):
        """
        I return the obsel type of this obsel.
        """
        tmodel = self.trace.model
        if tmodel and hasattr(tmodel, 'get'):
            for typ in self.state.objects(self.uri, RDF.type):
                ret = tmodel.get(typ)
                # must be a .trace_model.ObselTypeMixin
                if ret is not None:
                    return ret
        return None

    def get_begin(self):
        """
        I return the begin timestamp of the obsel.
        """
        return int(self.state.value(self.uri, KTBS.hasBegin))

    def get_begin_dt(self):
        """
        I return the begin timestamp of the obsel.

        We use a better implementation than the standard one.
        """
        return lit2datetime(self.state.value(self.uri, KTBS.hasBeginDT))

    def get_end(self):
        """
        I return the end timestamp of the obsel.
        """
        return int(self.state.value(self.uri, KTBS.hasEnd))

    def get_end_dt(self):
        """
        I return the end timestamp of the obsel.
        """
        return lit2datetime(self.state.value(self.uri, KTBS.hasEndDT))

    def get_subject(self):
        """
        I return the subject of the obsel.
        """
        ret = self.state.value(self.uri, KTBS.hasSubject)
        if ret is not None:
            ret = unicode(ret)
        return ret

    def iter_source_obsels(self):
        """
        I iter over the source obsels of the obsel.
        """
        factory = self.factory
        for i in self.state.objects(self.uri, KTBS.hasSourceObsel):
            yield factory(i, KTBS.Obsel)

    def iter_attribute_types(self):
        """
        I iter over all attribute types set for this obsel.
        """
        query_str = """
            SELECT DISTINCT ?at
            WHERE {
                <%s> ?at ?value .
                OPTIONAL {
                    ?value <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> ?t
                }
                FILTER (!bound(?t))
            }
        """ % self.uri
        factory = self.factory
        for atype, in self.state.query(query_str): #/!\ returns 1-uples
            if not atype.startswith(KTBS.uri) and atype != RDF.type:
                yield factory(atype, KTBS.AttributeType)

    def iter_relation_types(self):
        """
        I iter over all outgoing relation types for this obsel.
        """
        query_str = """
            SELECT DISTINCT ?rt
            WHERE {
                <%s> ?rt ?related .
                ?related <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> ?t .
            }
        """ % self.uri
        factory = self.factory
        for rtype, in self.state.query(query_str): #/!\ returns 1-uples
            yield factory(rtype, KTBS.RelationType)

    def iter_related_obsels(self, rtype):
        """
        I iter over all obsels pointed by an outgoing relation.
        """
        rtype = coerce_to_uri(rtype, self.uri)
        query_str = """
            SELECT ?related
            WHERE {
                <%s> <%s> ?related .
                ?related <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> ?t .
            }
        """ % (self.uri, rtype)
        factory = self.factory
        for related, in self.state.query(query_str): #/!\ returns 1-uples
            yield factory(related, KTBS.Obsel)

    def iter_inverse_relation_types(self):
        """
        I iter over all incoming relation types for this obsel.
        """
        query_str = """
            SELECT DISTINCT ?rt
            WHERE {
                ?relating ?rt <%s> .
                ?relating <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> ?t .
            }
        """ % self.uri
        factory = self.factory
        for rtype, in self.state.query(query_str): #/!\ returns 1-uples
            yield factory(rtype, KTBS.RelationType)

    def iter_relating_obsels(self, rtype):
        """
        I iter over all incoming relation types for this obsel.
        """
        rtype = coerce_to_uri(rtype, self.uri)
        query_str = """
            SELECT ?relating
            WHERE {
                ?relating <%s> <%s> .
                ?relating <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> ?t .
            }
        """ % (rtype, self.uri)
        factory = self.factory
        for relating, in self.state.query(query_str): #/!\ returns 1-uples
            yield factory(relating, KTBS.Obsel)

    def get_attribute_value(self, atype):
        """
        I return the value of the given attribut type for this obsel, or None.
        """
        atype = coerce_to_uri(atype, self.uri)
        ret = self.state.value(self.uri, atype)
        if isinstance(ret, Literal):
            ret = ret.toPython()
        return ret

    # TODO SOON implement attribute and relation methods (set_, del_, add_)


class ObselProxy(ObselMixin, ICore):
    """I provide a lightweight implementation of ktbs:Obsel.

    As obsel descriptions can be found in obsel collections, this class provides
    the Obsel API atop an obsel collection; t
    """

    def __init__(self, uri, collection, host_graph, host_parameters):
        # not calling parents __init__ #pylint: disable=W0231
        self.uri = coerce_to_uri(uri, collection.uri)
        self.collection = collection
        self.host_graph = host_graph
        self.host_parameters = host_parameters
        if __debug__:
            self._readonly_graph = ReadOnlyGraph(host_graph)

    def __str__(self):
        return "<%s>" % self.uri

    ######## ICore implementation ########

    def factory(self, uri, _rdf_type=None, _no_spawn=False):
        """I implement :meth:`.cores.ICore.factory`.

        I simply rely on the factory of my obsel collection.
        """
        return self.collection.factory(uri, _rdf_type, _no_spawn)

    def get_state(self, parameters=None):
        """I implement :meth:`.cores.ICore.get_state`.

        I simply return
        """
        if parameters is not None:
            raise InvalidParametersError(" ".join(parameters.keys))
        if __debug__:
            return self._readonly_graph
        else:
            return self.host_graph

    def force_state_refresh(self, parameters=None):
        """I implement `interface.ICore.force_state_refresh`.

        I simply force a state refresh on my host.
        """
        if parameters is not None:
            raise InvalidParametersError(" ".join(parameters.keys))
        self.collection.force_state_refresh(self.host_parameters)

    def edit(self, parameters=None, clear=False, _trust=False):
        """I implement :meth:`.cores.ICore.edit`.

        If `self.host_graph` is the complete obsel collection (`host_parameters`
        is None), edit it directly;
        else, try to get "proper" obsel resource and edit it.

        Note that the `clear` argument is not supported in all situations (as
        host graph may be bigger than the obsel's state);
        if you need a clear edit context, you should use a "proper" obsel::

            obs = obs.factory(obs.uri)
            graph = obs.get_state()

        and then ensure that you fill the edit context with what you got from
        the proper obsel's state.
        """
        if parameters is not None:
            raise InvalidParametersError(" ".join(parameters.keys()))
        if self.host_parameters is None:
            return self.collection.edit(None, clear, _trust)
        else:
            if clear:
                # this is unsafe, as get_state returned the host graph,
                # while the edit context will rely only of this obsel's graph
                raise ValueError("I do not support *clear* edit context "
                                 "(see docstring).")
            proper = self.collection.factory(self.uri, KTBS.Obsel)
            if proper is None:
                raise ValueError("Could not get proper obsel %s" % self)
            assert isinstance(proper, ObselMixin)  and  proper.uri == self.uri
            return proper.edit(None, False, _trust)

    def post_graph(self, graph, parameters=None,
                   _trust=False, _created=None, _rdf_type=None):
        """I implement :meth:`.cores.ICore.post_graph`.

        Obsels do not support post_graph.
        """
        # unused arguments #pylint: disable=W0613
        raise MethodNotAllowedError("Can not post to obsel %s" % self)

    def delete(self, parameters=None, _trust=False):
        """I implement :meth:`.cores.ICore.delete`.

        Delegate to proper obsel resource.
        """
        proper = self.collection.factory(self.uri, KTBS.Obsel)
        if proper is None:
            raise ValueError("Could not get proper obsel %s" % self)
        assert isinstance(proper, ObselMixin)  and  proper.uri == self.uri
        return proper.delete(None, parameters, _trust)
