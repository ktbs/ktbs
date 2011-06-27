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
I provide the client implementation of a trace Base.
"""
#from httplib2 import Http
from rdflib import RDF
#from rdfrest.client import ProxyStore

from ktbs.client.resource import Resource, RESOURCE_MAKER
from ktbs.common.base import BaseMixin
from ktbs.namespaces import KTBS

class Base(BaseMixin, Resource):
    """I implement a client proxy on the root of a kTBS.
    """

    # TODO implement create_X


RESOURCE_MAKER[KTBS.Base] = Base

_RDF_TYPE = RDF.type

# the following import ensures that required classes are registered in
# RESOURCE_MAKER (Model, StoredTrace, ComputedTrace, Method)
#import ktbs.client.method #pylint: disable-msg=W0611
import ktbs.client.model #pylint: disable-msg=W0611
import ktbs.client.trace #pylint: disable-msg=W0611,W0404
# NB: we have to disable pylint W0611 (Unused import) and W0404 (Reimport)
