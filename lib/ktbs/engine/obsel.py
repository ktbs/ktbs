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

"""
I provide the implementation of ktbs:Obsel .
"""
from rdflib import Literal, URIRef, XSD
from rdflib.plugins.sparql.processor import prepareQuery
import re

from datetime import datetime

from rdfrest.util.iso8601 import UTC
from rdfrest.util import bounded_description, make_fresh_uri, parent_uri
from .resource import KtbsResource
from ..api.obsel import ObselMixin
from ..namespace import KTBS, RDF
from ..utils import SKOS
from ..time import get_converter_to_unit, lit2datetime #pylint: disable=E0611



# pylint is confused by a module named time (as built-in module)
    

class Obsel(ObselMixin, KtbsResource):
    """
    I provide the implementation of ktbs:Obsel .
    """

    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.Obsel

    RDF_RESERVED_NS =     [ KTBS ]
    RDF_CREATABLE_OUT =   [ KTBS.hasTrace, ]
    RDF_EDITABLE_OUT =    [ KTBS.hasBegin, KTBS.hasBeginDT, KTBS.hasEnd,
                            KTBS.hasEndDT, KTBS.hasSubject, KTBS.hasSourceObsel,
                            ]
    RDF_CARDINALITY_OUT = [ (KTBS.hasBegin, 1, 1),
                            (KTBS.hasBeginDT, 0, 1),
                            (KTBS.hasEnd, 1, 1),
                            (KTBS.hasEndDT, 0, 1),
                            (KTBS.hasSubject, 0, 1),
                            (KTBS.hasTrace, 1, 1),
                            ]
    RDF_TYPED_PROP =      [ (KTBS.hasBegin,   "literal", XSD.integer),
                            (KTBS.hasBeginDT, "literal", XSD.dateTime),
                            (KTBS.hasEnd,     "literal", XSD.integer),
                            (KTBS.hasEndDT,   "literal", XSD.dateTime),
                            #(KTBS.hasTrace,   "uri"), # not required, see below
                            ]
    # the type "uri" for KTBS.hasTrace is not required, because
    # complete_new_graph will add the correct ktbs:hasTrace arc,
    # so if the graph also contains ktbs:hasTrace pointing to a literal,
    # this will violate the cardinality constraint.

    @classmethod
    def complete_new_graph(cls, service, uri, parameters, new_graph,
                           resource=None):
        """I implement :meth:`ILocalCore.complete_new_graph`.

        I add some information than can be infered from new_graph and from
        the trace of the obsel.
        """
        super(Obsel, cls).complete_new_graph(service, uri, parameters,
                                              new_graph, resource)

        trace = cls._get_trace_from_uri(service, uri)

        # add link to trace in case it is missing
        new_graph.add((uri, KTBS.hasTrace, trace.uri))

        # add default type if none is provided
        obsel_type = new_graph.value(uri, RDF.type)
        if obsel_type is None:
            new_graph.add((uri, RDF.type, KTBS.Obsel))

        # add default subject if no subject is provided
        subject = new_graph.value(uri, KTBS.hasSubject)
        if subject is None:
            default_subject = trace.get_default_subject()
            if default_subject is not None:
                new_graph.add((uri, KTBS.hasSubject, Literal(default_subject)))

        # compute begin and/or end if beginDT and/or endDT are provided
        delta2unit = None
        origin = None
        begin_dt = lit2datetime(new_graph.value(uri, KTBS.hasBeginDT))
        end_dt = lit2datetime(new_graph.value(uri, KTBS.hasEndDT))
        if begin_dt or end_dt:
            delta2unit = get_converter_to_unit(trace.unit)
            origin = lit2datetime(trace.origin)
            if origin is not None:
                if delta2unit is not None:
                    if begin_dt is not None:
                        begin = delta2unit(begin_dt - origin)
                        new_graph.add((uri, KTBS.hasBegin, Literal(begin)))
                    if end_dt is not None:
                        end = delta2unit(end_dt - origin)
                        new_graph.add((uri, KTBS.hasEnd, Literal(end)))


        # complete missing begin with current date
        begin = new_graph.value(uri, KTBS.hasBegin)
        if begin is None:
            delta2unit = delta2unit or get_converter_to_unit(trace.unit)
            origin = origin or lit2datetime(trace.origin)
            begin = Literal(delta2unit(_NOW(UTC) - origin))
            new_graph.add((uri, KTBS.hasBegin, begin))

        # complete missing end if only begin is provided
        end = new_graph.value(uri, KTBS.hasEnd)
        if end is None:
            new_graph.add((uri, KTBS.hasEnd, begin))
                      

    @classmethod
    def check_new_graph(cls, service, uri, parameters, new_graph,
                        resource=None, added=None, removed=None):
        """I implement :meth:`ILocalCore.check_new_graph`.

        I check what the mixins can not check.
        """
        # unused arguments #pylint: disable=W0613

        diag = super(Obsel, cls).check_new_graph(
            service, uri, parameters, new_graph, resource, added, removed)

        begin = new_graph.value(uri, KTBS.hasBegin)
        end = new_graph.value(uri, KTBS.hasEnd)
        try:
            begin = int(begin)
            end = int(begin)
            if end < begin:
                diag.append("End timestamp is before begin timestamp [%s,%s]"
                            % (begin, end))
        except ValueError:
            diag.append("Can not convert timestamps to int: [%s,%s]"
                        % (begin, end))

        # TODO SOON check that graph only contains a bounded description
        # of the obsel
        return diag

    @classmethod
    def mint_uri(cls, target, new_graph, created, basename="o", suffix=""):
        """I implement :meth:`rdfrest.cores.local.ILocalCore.mint_uri`.

        I use the skos:prefLabel of the resource to mint a URI, else the
        basename.
        """
        # Do NOT call super method, as this is the base implementation.
        label = (new_graph.value(created, SKOS.prefLabel)
                 or basename).lower()
        prefix = "%s%s-" % (target.uri, _NON_ALPHA.sub("-", label))
        return make_fresh_uri(None, prefix, suffix, target._check_new_obsel)

    def ack_edit(self, parameters, prepared):
        """I override :meth:`rdfrest.cores.local.ILocalCore.ack_edit`
        to force my trace's obsel_collection to change its etags.
        """
        trace = self._get_trace_from_uri(self.service, self.uri)
        with trace.obsel_collection.edit(_trust=True) as editable:
            pass

    def ack_delete(self, parameters):
        """
        I implement :meth:`rdfrest.cores.local.ILocalCore.ack_delete`.

        :param parameters:
        :return:
        """
        trace = self._get_trace_from_uri(self.service, self.uri)
        with trace.obsel_collection.edit(_trust=True) as editable:
            editable.remove((self.uri, KTBS.hasTrace, trace.uri))

    ######## Private methods ########

    @classmethod
    def _get_trace_from_uri(cls, service, obsel_uri):
        """I return the trace owning a given obsel.
        """
        ret = service.get(URIRef(parent_uri(obsel_uri)))
        assert ret.RDF_MAIN_TYPE in (KTBS.StoredTrace, KTBS.ComputedTrace), \
            (ret.RDF_MAIN_TYPE, obsel_uri)
        return ret
        # must be a .trace.AbstractTrace



def get_obsel_bounded_description(node, graph, fill=None):
    """I override :func:`rdfrest.util.bounded_description` for obsels.

    In order to clearly differenciate attributes from relations,
    related obsels must be linked to the trace by the ktbs:hasTrace.

    :param node: the node (uri or blank) to return a description of
    :param graph: the graph from which to retrieve the description
    :param fill: if provided, fill this graph rather than a fresh one, and return it
    """
    ret = bounded_description(node, graph, fill)
    trace_uri = ret.value(node, KTBS.hasTrace)
    add = ret.add
    for other, in graph.query(_RELATED_OBSELS, initBindings = { "obs": node }):
        add((other, KTBS.hasTrace, trace_uri))
    return ret


_RELATED_OBSELS = prepareQuery("""
    SELECT DISTINCT ?other
    {
        { ?obs ?pred ?other . }
        UNION
        { ?other ?pred ?obs . }
        ?obs <%s> ?trace .
        ?other <%s> ?trace .
    }
    """ % (KTBS.hasTrace, KTBS.hasTrace))

_NON_ALPHA = re.compile(r'[^\w]+')
_NOW = datetime.now
