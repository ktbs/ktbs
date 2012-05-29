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
I provide the client implementation of Obsel
"""
from ktbs.client.resource import register, Resource
from ktbs.common.obsel import ObselMixin
from ktbs.namespaces import KTBS


class Obsel(ObselMixin, Resource):
    """TODO docstring"""
    # TODO implement client-specifid methods

    RDF_MAIN_TYPE = KTBS.Obsel

register(Obsel)

# the following import ensures that required classes are registered as well
# (AttributeType, RelationType)
import ktbs.client.model #pylint: disable-msg=W0611
# NB: we have to disable pylint W0611 (Unused import)
