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
I provide the client implementation of trace models and their elements.
"""
#pylint: disable-msg=R0904
#    too many public methods

from ktbs.client.resource import Resource, RESOURCE_MAKER
from ktbs.common.model import (ModelMixin, AttributeTypeMixin, ObselTypeMixin,
                               RelationTypeMixin)
from ktbs.namespaces import KTBS


class Model(ModelMixin, Resource):
    """TODO docstring"""
    pass

class AttributeType(AttributeTypeMixin, Resource):
    """TODO docstring"""
    pass

class ObselType(ObselTypeMixin, Resource):
    """TODO docstring"""
    pass

class RelationType(RelationTypeMixin, Resource):
    """TODO docstring"""
    pass


RESOURCE_MAKER[KTBS.Model] = Model
RESOURCE_MAKER[KTBS.ObselType] = ObselType
RESOURCE_MAKER[KTBS.AttributeType] = AttributeType
RESOURCE_MAKER[KTBS.RelationType] = RelationType
