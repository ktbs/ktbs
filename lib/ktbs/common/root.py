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
from rdfrest.utils import coerce_to_uri

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
            yield make_resource(obs, _BASE)

    def get_base(self, id):
        """
        I return the base corresponding to the given URI.
        """
        #pylint: disable-msg=W0622
        #  Redefining built-in id
        base_uri = coerce_to_uri(id, self.uri)
        return self.make_resource(base_uri, _BASE)

    def iter_builtin_methods(self):
        """
        I list all the builtin methods implemented by this kTBS.
        """
        make_resource = self.make_resource
        for obs in self.graph.objects(self.uri, _HAS_BUILTIN_METHOD):
            yield make_resource(obs, _METHOD)
        

_BASE = KTBS.Base
_HAS_BASE = KTBS.hasBase    
_HAS_BUILTIN_METHOD = KTBS.hasBuiltinMethod    
_METHOD = KTBS.Method
