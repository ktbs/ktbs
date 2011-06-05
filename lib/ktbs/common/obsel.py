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
from rdflib import RDF, URIRef

from ktbs.common.utils import coerce_to_uri, extend_api
from ktbs.iso8601 import parse_date
from ktbs.namespaces import KTBS

@extend_api
class ObselMixin(object):
    """
    I provide the pythonic interface to obsels.
    """
    def get_trace(self):
        """
        I return the trace containing this obsel.
        """
        return self.make_resource(self.get_object(_HAS_TRACE))

    def get_obsel_type(self):
        """
        I return the obsel type of this obsel.
        """
        tmodel = self.trace.trace_model
        for typ in self.iter_objects(_RDF_TYPE):
            ret = tmodel.get(typ)
            if ret is not None:
                return ret

    def get_begin(self):
        """
        I return the begin timestamp of the obsel.
        """
        return int(self.get_object(_HAS_BEGIN))

    def get_begin_dt(self):
        """
        I return the begin timestamp of the obsel.

        We use a better implementation than the standard one.
        """
        return parse_date(self.get_object(_HAS_BEGIN_DT))

    def get_end(self):
        """
        I return the end timestamp of the obsel.
        """
        return int(self.get_object(_HAS_END))

    def get_end_dt(self):
        """
        I return the end timestamp of the obsel.
        """
        return parse_date(self.get_object(_HAS_END_DT))

    def get_subject(self):
        """
        I return the subject of the obsel.
        """
        return self.get_object(_HAS_SUBJECT)

    @property
    def outgoing(self):
        """
        I provide mapping-like access to outgoing properties.

        When iterated, I yield all outgoing properties of this object
        (relation types, attribute types and other RDF properties).

        When indexed by a given property (using [property]), I iter over all
        the values of that property. Indices can be RelationTypes,
        AttributeTYpes, RDF.Nodes or URIs as strings.
        """
        return _PropertyMapping(self, 1)

    @property
    def incoming(self):
        """
        I provide mapping-like access to incomping properties.

        :see-also: `outgoing`
        """
        return _PropertyMapping(self, -1)

    # TODO MAJOR implement attribute and relation iter_ methods



class _PropertyMapping(object):
    """
    I implement mapping-like access to properties of an obsels.
    """
    #pylint: disable-msg=R0903

    def __init__(self, obsel, direction):
        self.obsel = obsel
        self.type_getter = obsel.trace.trace_model.get
        query_str = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT DISTINCT ?p
        WHERE { GRAPH <%%s> {
            %s
            FILTER (?p != rdf:type
                && !regex(str(?p), "^http://liris.cnrs.fr/silex/2009/ktbs#")
            )
        }}"""
        if direction == 1:
            query_str %= "<%s> ?p []"
            self.iter_values = obsel.iter_objects
        else:
            assert direction == -1
            query_str %= "[] ?p <%s>"
            self.iter_values = obsel.iter_subjects
        query_str %= (obsel.uri, )
        self.iter_pred = query_str

    def __iter__(self):
        for pred, in self.obsel.graph.query(self.iter_pred):
            yield self.type_getter(pred) or pred

    def __getitem__(self, predicate):
        make_resource = self.obsel.make_resource
        for i in self.iter_values(coerce_to_uri(predicate)):
            if isinstance(i, URIRef):
                i = make_resource(i) or i
            yield i

_HAS_BEGIN = KTBS.hasBegin
_HAS_BEGIN_DT = KTBS.hasBeginDT
_HAS_END = KTBS.hasEnd
_HAS_END_DT = KTBS.hasEndDT
_HAS_SUBJECT = KTBS.hasSubject
_HAS_TRACE = KTBS.hasTrace
_RDF_TYPE = RDF.type
