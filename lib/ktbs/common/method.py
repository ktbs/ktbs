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
from ktbs.common.utils import extend_api
from ktbs.namespaces import KTBS

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
        for parameter in self.iter_objects(_HAS_PARAMETER):
            key, value = parameter.split("=", 1)
            parameters[key] = value
        return parameters

    # TODO MAJOR implement the parameter related iter_ methods


@extend_api
class MethodMixin(WithParametersMixin):
    """
    I provide the pythonic interface to methods.
    """

    def get_inherited(self):
        """
        I return the inherited method.

        NB: for built-in methods, I return the URI itself.
        """
        method_uri = self.get_object(_INHERITS)
        return self.make_resource(method_uri) or method_uri

    def _get_inherited_parameters(self):
        """
        Required by WithParametersMixin.
        """
        return getattr(self.inherited, "parameters", None) or {}


_HAS_PARAMETER = KTBS.hasParameter
_INHERITS = KTBS.inherits
