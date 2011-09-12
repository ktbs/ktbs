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
from rdflib import RDF, URIRef
from urlparse import urldefrag

from ktbs.common.resource import ResourceMixin
from ktbs.common.utils import extend_api
from ktbs.namespaces import KTBS
from rdfrest.utils import coerce_to_uri

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
        return iter(self._graph.query(query_template % self.uri))
            
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

    def get(self, id):
        """
        Return one of the element contained in the base.
        """
        #pylint: disable-msg=W0622
        #  Redefining built-in id
        elt_uri = coerce_to_uri(id, self.uri)
        typ = self._graph.value(elt_uri, _RDF_TYPE)
        if typ not in (_STORED_TRACE, _COMPUTED_TRACE, _MODEL, _METHOD):
            return None
        else:
            return self.make_resource(elt_uri, typ)

    def get_root(self):
        """
        Return the root of the KTBS containing this base.
        """
        root_uri = URIRef("..", self.uri)
        return self.make_resource(root_uri, _ROOT)


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
        cut = urldefrag(self.uri)[0].rfind("/", 0, -1)
        base_uri = self.uri[:cut+1]
        return self.make_resource(base_uri, _BASE)

        
_CONTAINS = KTBS.contains    
_BASE = KTBS.Base
_STORED_TRACE = KTBS.StoredTrace
_COMPUTED_TRACE = KTBS.ComputedTrace
_MODEL = KTBS.TraceModel
_METHOD = KTBS.Method
_RDF_TYPE = RDF.type
_ROOT = KTBS.KtbsRoot
