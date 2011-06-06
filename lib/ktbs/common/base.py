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
I provide the pythonic interface to bases.
"""
from rdflib import RDF
from urlparse import urldefrag, urljoin

from ktbs.common.resource import ResourceMixin
from ktbs.common.utils import coerce_to_uri, extend_api
from ktbs.namespaces import KTBS

@extend_api
class BaseMixin(ResourceMixin):
    """
    I provide the pythonic interface common to bases.
    """

    def _iter_contained(self):
        """
        Yield the URI and type of every element of this base.
        """
        query_template = """
            PREFIX k: <http://liris.cnrs.fr/silex/2009/ktbs#>
            SELECT DISTINCT ?s ?t
            WHERE { <%s> k:contains ?s . ?s a ?t . }
        """
        return iter(self.graph.query(query_template % self.uri))
            
    def iter_traces(self):
        """
        Iter over all the traces (stored or computed) of this base.
        """
        make_resource = self.make_resource
        for uri, typ in self._iter_contained():
            if typ == _STORED_TRACE or typ == _COMPUTED_TRACE:
                yield make_resource(uri, typ)

    def iter_models(self):
        """
        Iter over all the trace models of this base.
        """
        make_resource = self.make_resource
        for uri, typ in self._iter_contained():
            if typ == _MODEL:
                yield make_resource(uri, typ)

    def iter_methods(self):
        """
        Iter over all the methods of this base.
        """
        make_resource = self.make_resource
        for uri, typ in self._iter_contained():
            if typ == _METHOD:
                yield make_resource(uri, typ)

    def get(self, uri):
        """
        Return one of the element contained in the base.
        """
        elt_uri = coerce_to_uri(urljoin(self.uri, uri))
        typ = next(self.graph.objects(self.uri, _RDF_TYPE), None)
        if typ not in (_STORED_TRACE, _COMPUTED_TRACE, _MODEL, _METHOD):
            return None
        else:
            return self.make_resource(elt_uri, typ)


@extend_api
class InBaseMixin(ResourceMixin):
    """
    Common mixin for all elements of a trace base.
    """
    #pylint: disable-msg=R0903
    # Too few public methods

    def get_base(self):
        """
        Return the trace base this element belongs to.
        """
        base_uri = urldefrag(self.uri)[0].rfind("/", 0, -1)
        return self.make_resource(base_uri, _BASE)

        
_CONTAINS = KTBS.contains    
_BASE = KTBS.Base
_STORED_TRACE = KTBS.StoredTrace
_COMPUTED_TRACE = KTBS.ComputedTrace
_MODEL = KTBS.TraceModel
_METHOD = KTBS.Method
_RDF_TYPE = RDF.type
