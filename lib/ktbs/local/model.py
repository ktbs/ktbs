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
I provide the local implementation of ktbs:TraceModel .
"""
from rdflib import RDF

from ktbs.common.model import ModelMixin, ObselTypeMixin, AttributeTypeMixin, \
    RelationTypeMixin
from ktbs.common.utils import extend_api
from ktbs.local.base import InBaseMixin
from ktbs.local.resource import Resource
from ktbs.namespaces import KTBS

@extend_api
class Model(ModelMixin, InBaseMixin, Resource):
    """I implement a local KTBS trace model.
    """

    # KTBS API #

    def make_resource(self, uri, node_type=None, _graph=None):
        """I override make_resource in order to provide "sub-resources".
        """
        if not uri.startswith(self.uri):
            return super(Model, self).make_resource(uri, node_type)
        # TODO use node_type and ignore graph
        for rdf_type in self._graph.objects(uri, RDF.type):
            if rdf_type == KTBS.ObselType:
                return ObselType(self, uri)
            elif rdf_type == KTBS.AttributeType:
                return AttributeType(self, uri)
            elif rdf_type == KTBS.RelationType:
                return RelationType(self, uri)
        raise ValueError("resource not found: <%s>" % uri)
            
    # RDF-REST API #

    RDF_MAIN_TYPE = KTBS.TraceModel

    RDF_PUTABLE_OUT = [KTBS.hasParentModel]

class _ModelResource(object):
    """I provide the interface expected by `~lib.ktbs.common`:mod: mixins
    for resources hosted inside a TraceModel.
    """
    # too few public methods (abstract) #pylint: disable=R0903
    def __init__(self, model, uri):
        self.uri = uri
        self._model = model
        self._graph = model._graph #pylint: disable=W0212

    @property
    def _edit(self):
        "to please common mixins"
        return self._model._edit #pylint: disable=W0212

    def make_resource(self, uri, node_type=None, graph=None):
        "to please common mixins"
        return self._model.make_resource(uri, node_type, graph)

@extend_api
class ObselType(ObselTypeMixin, _ModelResource):
    """
    I provide the pythonic interface common to ktbs trace models.
    """
    pass

@extend_api
class AttributeType(AttributeTypeMixin, _ModelResource):
    """
    I provide the pythonic interface common to ktbs trace models.
    """
    pass

@extend_api
class RelationType(RelationTypeMixin, _ModelResource):
    """
    I provide the pythonic interface common to ktbs trace models.
    """
    pass
