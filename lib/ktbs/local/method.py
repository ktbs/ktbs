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

from ktbs.common.method import MethodMixin
from ktbs.common.utils import extend_api
from ktbs.local.base import BaseResource
from ktbs.local.service import KtbsService
from ktbs.namespaces import KTBS

@extend_api
class Method(MethodMixin, BaseResource):
    """
    I provide the pythonic interface common to ktbs root.
    """

    RDF_MAIN_TYPE = KTBS.Method

    RDF_PUTABLE_OUT = [ KTBS.hasParentMethod, KTBS.hasParameter, ]
    RDF_CARDINALITY_OUT = [ (KTBS.hasParentMethod, 1, 1) ]
    # KTBS API #

    # RDF-REST API #

    @classmethod
    def check_new_graph(cls, uri, new_graph,
                        resource=None, added=None, removed=None):
        """I overrides :meth:`rdfrest.resource.Resource.check_new_graph` to
        check the check that parent and parameters are acceptable
        """
        # just checking their syntax for the moment
        errors = []
        errors = super(Method, cls).check_new_graph(uri, new_graph, resource,
                                                    added, removed)
        if errors is None:
            errors = []
        else:
            errors = [errors]

        parent = new_graph.value(uri, KTBS.hasParentMethod)
        base = new_graph.value(None, KTBS.contains, uri)
        if not parent.startswith(base) \
        and not KtbsService.has_builtin_method(parent):
            errors.append("Parent method not supported: <%s>" % parent) 

        for param in new_graph.objects(uri, KTBS.hasParameter):
            if not isinstance(param, Literal):
                errors.append("Parameters should be literals; "
                              "got <%s>" % param)
            if "=" not in param:
                errors.append("Parameter is ill-formatted: %r" % str(Literal))

        if errors:
            return "\n".join(errors)
        else:
            return None


