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
I provide the pythonic interface to ktbs root.
"""
from ktbs.common.utils import extend_api
from ktbs.namespaces import KTBS

@extend_api
class KtbsRootMixin(object):
    """
    I provide the pythonic interface common to ktbs root.
    """
    #pylint: disable-msg=R0903
    #    too few public methods

    def iter_bases(self):
        """
        I iter over all elements owned by this base.
        """
        make_resource = self.make_resource
        for obs in self.graph.objects(self.uri, _HAS_BASE):
            yield make_resource(obs)

_HAS_BASE = KTBS.hasBase    
