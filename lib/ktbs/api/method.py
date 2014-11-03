# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
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
I provide the pythonic interface of ktbs:Method.
"""
from rdflib import Literal

from rdfrest.cores.factory import factory as universal_factory
from rdfrest.util import coerce_to_uri
from .base import InBaseMixin
from ..namespace import KTBS
from rdfrest.wrappers import register_wrapper
from ..utils import extend_api


@extend_api
class WithParametersMixin(object):
    """
    I provide property `parameters` for both Method and ComputedTrace.

    I rely on method _get_inherited_parameters, which must return a (possibly
    empty) fresh dict.
    """

    ######## Abstract kTBS API ########

    def iter_parameters(self, include_inherited=True):
        """I iter over the parameter of this resource.
        """
        if include_inherited:
            for i in self.parameters_as_dict:
                yield i
        else:
            for parameter in self.state.objects(self.uri, KTBS.hasParameter):
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
        for i in self.state.objects(self.uri, KTBS.hasParameter):
            akey, _ = i.split("=", 1)
            if akey == key:
                parameter = i
                break

        with self.edit(_trust=True) as graph:
            if parameter is not None:
                graph.remove((self.uri, KTBS.hasParameter, parameter))
            if value is not None:
                graph.add((self.uri, KTBS.hasParameter,
                                Literal("%s=%s" % (key, value))))
        
    def del_parameter(self, key):
        """
        I delete a parameter value.
        """
        self.set_parameter(key, None)

    ######## Extension to the abstract kTBS API ########

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
        for parameter in self.state.objects(self.uri, KTBS.hasParameter):
            key, value = parameter.split("=", 1)
            parameters[key] = value
        return parameters


@register_wrapper(KTBS.Method)
@extend_api
class MethodMixin(WithParametersMixin, InBaseMixin):
    """
    I provide the pythonic interface of ktbs:Method.
    """

    ######## Abstract kTBS API ########

    def get_parent(self):
        """
        I return the inherited method.
        """
        method_uri = self.state.value(self.uri, KTBS.hasParentMethod)
        return universal_factory(method_uri)

    def set_parent(self, method):
        """
        I set the parent method.
        """
        method_uri = coerce_to_uri(method, self.uri)
        # checking that method_uri is a valid parent is a bit tricky
        # so we leave it to the implementation to check it:
        # we use an *untrusted* edit context
        with self.edit() as graph:
            graph.set((self.uri, KTBS.hasParentMethod, method_uri))
        self._ack_change_parameters()

    ######## Extension to the abstract kTBS API  ########

    def iter_used_by(self):
        """I iter over all computed traces using this method
        """
        self.force_state_refresh() # as changes can come from other resources
        factory = self.factory
        for uri in self.state.subjects(KTBS.hasMethod, self.uri):
            yield factory(uri)
            # must be a .trace.AbstratcTraceMixin

    def iter_children(self):
        """I iter over all children method of this method
        """
        self.force_state_refresh() # as changes can come from other resources
        factory = self.factory
        for uri in self.state.subjects(KTBS.hasParentMethod, self.uri):
            child = factory(uri)
            assert isinstance(child, MethodMixin)
            yield child
        

    ######## Private methods ########

    def _get_inherited_parameters(self):
        """
        Required by WithParametersMixin.
        """
        return getattr(self.get_parent(), "parameters_as_dict", None) or {}
