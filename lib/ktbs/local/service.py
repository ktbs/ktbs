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
I implement KTBS as an `rdfrest.service.Service`:class.
"""

from rdfrest.service import Service

from ktbs.namespaces import KTBS

class KtbsService(Service):
    """The KTBS service.
    """
    
    @classmethod
    def builtin_methods(cls):
        """I return an iterable of all supported built-in methods.
        """
        # TODO MAJOR make it dynamic
        yield KTBS.filter
        yield KTBS.fusion
        yield KTBS.sparql
        yield KTBS.supermethod

# registering all resources classes
from ktbs.local.root import KtbsRoot
from ktbs.local.base import Base
from ktbs.local.model import Model
from ktbs.local.method import Method

KtbsService.register_root(KtbsRoot)
KtbsService.register(Base)
KtbsService.register(Model)
KtbsService.register(Method)
