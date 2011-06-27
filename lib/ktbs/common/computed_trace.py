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
I provide the pythonic interface to computed traces.
"""
from ktbs.common.method import WithParametersMixin
from ktbs.common.trace import TraceMixin
from ktbs.common.utils import coerce_to_uri, extend_api
from ktbs.namespaces import KTBS

@extend_api
class ComputedTraceMixin(TraceMixin, WithParametersMixin):
    """
    I provide the pythonic interface to computed traces.
    """
    def get_method(self):
        """
        I return the method of this trace.
        """
        method_uri = next(self.graph.objects(self.uri, _HAS_METHOD))
        return self.make_resource(method_uri)

    def set_method(self, method):
        """I set the method of this trace.
        method can be a Method or a URI; relative URIs are resolved againts
        this trace's URI.
        """
        method_uri = coerce_to_uri(method, self.uri)
        with self:
            self.graph.remove((self.uri, _HAS_METHOD, None))
            self.graph.add((self.uri, _HAS_METHOD, method_uri))

    def _get_inherited_parameters(self):
        """
        Required by WithParametersMixin.
        """
        return self.method.parameters_as_dict()


_HAS_METHOD = KTBS.hasMethod
