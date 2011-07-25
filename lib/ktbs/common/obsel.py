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
I provide the pythonic interface to obsels.
"""
from rdflib import Literal, RDF

from ktbs.common.resource import ResourceMixin
from ktbs.common.utils import extend_api
from ktbs.iso8601 import parse_date
from ktbs.namespaces import KTBS

from rdfrest.utils import coerce_to_uri

@extend_api
class ObselMixin(ResourceMixin):
    """
    I provide the pythonic interface to obsels.
    """
    def get_trace(self):
        """
        I return the trace containing this obsel.
        """
        return self.make_resource(self._graph.value(self.uri, _HAS_TRACE))

    def get_obsel_type(self):
        """
        I return the obsel type of this obsel.
        """
        tmodel = self.trace.trace_model
        for typ in self._graph.objects(self.uri, _RDF_TYPE):
            ret = tmodel.get(typ)
            if ret is not None:
                return ret

    def get_begin(self):
        """
        I return the begin timestamp of the obsel.
        """
        return int(self._graph.value(self.uri, _HAS_BEGIN))

    def get_begin_dt(self):
        """
        I return the begin timestamp of the obsel.

        We use a better implementation than the standard one.
        """
        return parse_date(self._graph.value(self.uri, _HAS_BEGIN_DT))

    def get_end(self):
        """
        I return the end timestamp of the obsel.
        """
        return int(self._graph.value(self.uri, _HAS_END))

    def get_end_dt(self):
        """
        I return the end timestamp of the obsel.
        """
        return parse_date(self._graph.value(self.uri, _HAS_END_DT))

    def get_subject(self):
        """
        I return the subject of the obsel.
        """
        return self._graph.value(self.uri, _HAS_SUBJECT)

    def iter_source_obsels(self):
        """
        I iter over the source obsels of the obsel.
        """
        make_resource = self.make_resource
        for i in self._graph.objects(self.uri, _HAS_SOURCE_OBSEL):
            yield make_resource(i, _OBSEL)

    def iter_attribute_types(self):
        """
        I iter over all attribute types set for this obsel.
        """
        query_str = """
            SELECT ?at
            WHERE {
                <%s> ?at ?value .
                OPTIONAL {
                    ?value <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> ?t
                }
                FILTER (!bound(?t))
            }
        """ % self.uri
        make_resource = self.make_resource
        for atype in self._graph.query(query_str):
            if not atype.startswith(KTBS) and atype != _RDF_TYPE:
                yield make_resource(atype, _ATTRIBUTE_TYPE)

    def iter_relation_types(self):
        """
        I iter over all outgoing relation types for this obsel.
        """
        query_str = """
            SELECT ?rt
            WHERE {
                <%s> ?rt ?related .
                ?related <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> ?t .
            }
        """ % self.uri
        make_resource = self.make_resource
        for rtype in self._graph.query(query_str):
            yield make_resource(rtype, _RELATION_TYPE)

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
        make_resource = self.make_resource
        for rtype in self._graph.query(query_str):
            yield make_resource(rtype, _OBSEL)

    def iter_inverse_relation_types(self):
        """
        I iter over all incoming relation types for this obsel.
        """
        query_str = """
            SELECT ?rt
            WHERE {
                ?relating ?rt <%s> .
                ?relating <http://liris.cnrs.fr/silex/2009/ktbs#hasTrace> ?t .
            }
        """ % self.uri
        make_resource = self.make_resource
        for rtype in self._graph.query(query_str):
            yield make_resource(rtype, _RELATION_TYPE)

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
        make_resource = self.make_resource
        for binding in self._graph.query(query_str):
            yield make_resource(binding[0], _OBSEL)

    def get_attribute_value(self, atype):
        """
        I return the value of the given attribut type for this obsel, or None.
        """
        atype = coerce_to_uri(atype, self.uri)
        ret = self._graph.value(self.uri, atype)
        if isinstance(ret, Literal):
            ret = ret.toPython()
        return ret

    # TODO MAJOR implement attribute and relation methods (set_, del_, add_)


_ATTRIBUTE_TYPE = KTBS.AttributeType
_HAS_BEGIN = KTBS.hasBegin
_HAS_BEGIN_DT = KTBS.hasBeginDT
_HAS_END = KTBS.hasEnd
_HAS_END_DT = KTBS.hasEndDT
_HAS_SOURCE_OBSEL = KTBS.hasSourceObsel
_HAS_SUBJECT = KTBS.hasSubject
_HAS_TRACE = KTBS.hasTrace
_OBSEL = KTBS.Obsel
_RDF_TYPE = RDF.type
_RELATION_TYPE = KTBS.RelationType
