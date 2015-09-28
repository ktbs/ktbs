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
I provide the implementation of ktbs:TraceModel .
"""
from .base import InBase
from ..api.trace_model import TraceModelMixin
from ..namespace import KTBS

class TraceModel(TraceModelMixin, InBase):
    """I provide the implementation of ktbs:TraceModel .
    """
    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.TraceModel

    RDF_EDITABLE_OUT = [ KTBS.hasParentModel, KTBS.hasUnit ]

    RDF_CARDINALITY_OUT = [ (KTBS.hasUnit, 0, 1) ]

    RDF_TYPED_PROP = [ (KTBS.hasParentModel, "uri"),
                       (KTBS.hasUnit,        "uri"),
                       ]
    @classmethod
    def complete_new_graph(cls, service, uri, parameters, new_graph,
                           resource=None):
        """I implement :meth:`ILocalCore.complete_new_graph`.

        At create time, I add default values for missing information about the
        trace model.
        """
        super(TraceModel, cls).complete_new_graph(service, uri, parameters,
                                                  new_graph, resource)
        if resource is None:
            unit = new_graph.value(uri, KTBS.hasUnit)
            if unit is None:
                new_graph.add((uri, KTBS.hasUnit, KTBS.millisecond))
