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
I provide the pythonic interface to methods.
"""
from rdflib import Literal

from ktbs.common.base import InBaseMixin
from ktbs.common.utils import extend_api
from ktbs.namespaces import KTBS
from rdfrest.utils import coerce_to_uri

@extend_api
class WithParametersMixin(object):
    """
    I provide property `parameters` for both Method and ComputedTrace.

    I rely on method _get_inherited_parameters, which must return a (possibly
    empty) fresh dict.
    """
    #pylint: disable=R0903
    #    too few public methods

    @property
    def parameters_as_dict(self):
        """
        I return a fresh dict of the parameters of this computed trace.

        NB: the keys and values of the dict are unicode. Values are *not*
        converted to the datatype expected by the method.

        NB: it is assumed that the RDF data is valid, especially that keys are
        not duplicated.
        """
        parameters = self._get_inherited_parameters()
        for parameter in self._graph.objects(self.uri, _HAS_PARAMETER):
            key, value = parameter.split("=", 1)
            parameters[key] = value
        return parameters

    def iter_parameters(self, include_inherited=True):
        """I iter over the parameter of this resource.
        """
        if include_inherited:
            for i in self.parameters_as_dict:
                yield i
        else:
            for parameter in self._graph.objects(self.uri, _HAS_PARAMETER):
                key, _ = parameter.split("=", 1)
                yield key

    def get_parameter(self, key):
        """
        I return a parameter value.
        """
        return self.parameters_as_dict.get(key)

    def set_parameter(self, key, value):
        """
        I set a parameter value.
        """
        if key in self._get_inherited_parameters():
            raise ValueError("Can not %s inherited parameter '%s'"
                             % ((value is None) and "delete" or "set", key))
        parameter = None
        for i in self._graph.objects(self.uri, _HAS_PARAMETER):
            akey, _ = i.split("=", 1)
            if akey == key:
                parameter = i
                break

        with self._edit as graph:
            if parameter is not None:
                graph.remove((self.uri, _HAS_PARAMETER, parameter))
            if value is not None:
                graph.add((self.uri, _HAS_PARAMETER,
                                Literal("%s=%s" % (key, value))))
        
    def del_parameter(self, key):
        """
        I delete a parameter value.
        """
        self.set_parameter(key, None)


@extend_api
class MethodMixin(WithParametersMixin, InBaseMixin):
    """
    I provide the pythonic interface to methods.
    """

    def get_parent(self):
        """
        I return the inherited method.
        """
        method_uri = self._graph.value(self.uri, _HAS_PARENT_METHOD)
        if method_uri is None:
            return None
        else:
            return self.make_resource(method_uri, _METHOD) or method_uri

    def set_parent(self, method):
        """
        I set the parent method.
        """
        # TODO include transaction management here?
        method = coerce_to_uri(method, self.uri)
        with self._edit as graph:
            graph.set((self.uri, _HAS_PARENT_METHOD, method))

    def _get_inherited_parameters(self):
        """
        Required by WithParametersMixin.
        """
        return getattr(self.inherited, "parameters_as_dict", None) or {}


_HAS_PARAMETER = KTBS.hasParameter
_HAS_PARENT_METHOD = KTBS.hasParentMethod
_METHOD = KTBS.Method
