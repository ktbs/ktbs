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
I provide the local implementation of ktbs:Method .
"""
from rdflib import Literal
from rdfrest.mixins import BookkeepingMixin, RdfPutMixin
from rdfrest.resource import compute_added_and_removed, Resource

from ktbs.common.method import MethodMixin
from ktbs.common.utils import extend_api
from ktbs.local.base import InBaseMixin
from ktbs.local.service import KtbsService
from ktbs.namespaces import KTBS

@extend_api
class Method(MethodMixin, InBaseMixin, BookkeepingMixin, RdfPutMixin,
             Resource):
    """I implement a local KTBS method.
    """

    RDF_MAIN_TYPE = KTBS.Method

    RDF_PUTABLE_OUT = [ KTBS.hasParentMethod, KTBS.hasParameter, ]
    RDF_CARDINALITY_OUT = [ (KTBS.hasParentMethod, 1, 1) ]
    # KTBS API #

    # RDF-REST API #

    @classmethod
    def check_new_graph(cls, service, uri, new_graph,
                        resource=None, added=None, removed=None):
        """I overrides :meth:`rdfrest.resource.Resource.check_new_graph` to
        check the check that parent and parameters are acceptable
        """
        added, removed = compute_added_and_removed(new_graph, resource, added,
                                                   removed)

        diag = super(Method, cls).check_new_graph(service, uri, new_graph,
                                                  resource, added, removed)

        if resource: # we only check values that were added/changed
            the_graph = added
        else:
            the_graph = new_graph
        parent_uri = the_graph.value(uri, KTBS.hasParentMethod)
        if parent_uri:
            base_uri = new_graph.value(None, KTBS.contains, uri)
            acceptable = parent_uri.startswith(base_uri) \
                or KtbsService.has_builtin_method(parent_uri)
            if not acceptable:
                diag.append("Invalid parent method: <%s>" % parent_uri)

        for param in the_graph.objects(uri, KTBS.hasParameter):
            if not isinstance(param, Literal):
                diag.append("Parameters should be literals; "
                              "got <%s>" % param)
            if "=" not in param:
                diag.append("Parameter is ill-formatted: %r" % str(Literal))

        return diag

