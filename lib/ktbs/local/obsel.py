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
I provide the local implementation of ktbs:StoredTrace and ktbs:ComputedTrace .
"""
from datetime import datetime
from rdflib import Literal, URIRef
from rdfrest.resource import ProxyResource
from rdfrest.utils import check_new, Diagnosis, make_fresh_uri, parent_uri

from ktbs.common.obsel import ObselMixin
from ktbs.common.utils import extend_api
from ktbs.local.resource import KtbsResourceMixin
from ktbs.local.trace import check_timestamp, cmp_timestamps, \
    complete_timestamp
from ktbs.namespaces import KTBS

@extend_api
class Obsel(ObselMixin, KtbsResourceMixin, ProxyResource):
    """
    I provide the pythonic interface common to ktbs root.
    """
    # KTBS API #


    # RDF-REST API #

    @classmethod
    def check_new_graph(cls, service, uri, new_graph,
                        resource=None, added=None, removed=None):
        """I override :meth:`rdfrest.resource.Resource.check_new_graph`.
        """
        assert (added is None) # obsels can not be PUT

        diag = Diagnosis("check_new_graph")

        trace = service.get(parent_uri(uri))
        subject = new_graph.value(uri, _HAS_SUBJECT)
        if subject is None:
            default = trace.get_default_subject()
            if default is None:
                diag.append("Can not determine obsel's subject")
            else:
                new_graph.add((uri, _HAS_SUBJECT, Literal(default)))

        origin = trace.get_origin(True)
        begin_i, begin_d, end_i, end_d = cls.get_timestamps(uri, new_graph)
        if begin_i is None and begin_d is None:
            diag.append("Unspecified or inconsistent begin timestamp")
        if end_i is None and end_d is None:
            diag.append("Unspecified or inconsistent end timestamp")
        if not check_timestamp(begin_i, begin_d, origin):
            diag.append("Inconsistent begin timestamps")
        if not check_timestamp(end_i, end_d, origin):
            diag.append("Inconsistent end timestamps")
        if cmp_timestamps(begin_i, begin_d, end_i, end_d, origin) > 0:
            diag.append("begin > end")
        if isinstance(origin, datetime):
            complete_timestamp(uri, begin_i, begin_d, origin,
                               new_graph.add, _HAS_BEGIN, _HAS_BEGIN_DT)
            complete_timestamp(uri, end_i, end_d, origin,
                               new_graph.add, _HAS_END, _HAS_END_DT)

        diag &= super(Obsel, cls).check_new_graph(service, uri, new_graph,
                                                 resource, added, removed)

        return diag

    @classmethod
    def mint_uri(cls, target, new_graph, created, suffix=""):
        """I override :meth:`rdfrest.resource.Resource.mint_uri`.
        
        I use check for the freshness of the URI in the trace's @obsels graph
        instead of the trace's main graph.
        """
        obsels = target.service.get(target.uri + "@obsels")
        obsels_graph = obsels._graph # protected member #pylint: disable=W0212
        prefix = "%so" % target.uri
        uri = URIRef("%s%s" % (prefix, suffix))
        if not check_new(obsels_graph, uri):
            prefix = "%s-" % prefix
            uri = make_fresh_uri(obsels_graph, prefix, suffix)
        print "===", uri
        return uri

    RDF_MAIN_TYPE = KTBS.Obsel

    RDF_POSTABLE_OUT = [ KTBS.hasTrace, ]

    RDF_PUTABLE_OUT = [ KTBS.hasBegin, KTBS.hasBeginDT, KTBS.hasEnd,
                        KTBS.hasEndDT, KTBS.hasSubject, KTBS.hasSourceObsel, ]
    RDF_CARDINALITY_OUT = [
        (KTBS.hasBegin, 1, 1),
        (KTBS.hasBeginDT, 0, 1),
        (KTBS.hasEnd, 1, 1),
        (KTBS.hasEndDT, 0, 1),
        (KTBS.hasSubject, 1, 1),
        ]
    # NB about cardinality: hasBegin, hasEnd and hasSubject are tagged as
    # mandatory, even if they may be ommited from the PUT/POSTed graph.
    # This is because check_new_graph will generate values for those
    # properties before CardinalityMixin gets to check them.
    # On the other hand, if check_new_graph has not enough information to
    # generate the values, CardinalityMixin will complain about missing
    # values.

    @classmethod
    def get_proxied_uri(cls, service, uri):
        """I override :meth:`rdfrest.resource.ProxyResource.get_proxied_uri`.

        I return the URI of my trace's obsel set, with appropriate params.
        """
        trace_uri, obsel_id = uri.rsplit("/", 1)
        return URIRef("%s/@obsels?id=%s" % (trace_uri, obsel_id))

    # other #

    @classmethod
    def get_timestamps(cls, uri, new_graph):
        """I retrieve obsel timestamps from new_graph.

        :rtype: a tuple of 4 Literals
        
        I provide hooks to allow plugins to define more ways to specify
        timestamps.

        If inconsistents timestamps are found, None should be returned for
        the corresponding bounds.
        """
        begin_i = new_graph.value(uri, _HAS_BEGIN)
        begin_d = new_graph.value(uri, _HAS_BEGIN_DT)
        end_i = new_graph.value(uri, _HAS_END)
        end_d = new_graph.value(uri, _HAS_END_DT)

        # TODO provide hook for plugins

        if end_i is None and end_d is None:
            end_i = begin_i
            end_d = begin_d
        return begin_i, begin_d, end_i, end_d

# TODO MINOR write unit tests to test all cases of obsel creation

_HAS_BEGIN = KTBS.hasBegin
_HAS_BEGIN_DT = KTBS.hasBeginDT
_HAS_END = KTBS.hasEnd
_HAS_END_DT = KTBS.hasEndDT
_HAS_SUBJECT = KTBS.hasSubject
