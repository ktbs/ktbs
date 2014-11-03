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
I provide the pythonic interface to kTBS built-in methods.
"""
from rdfrest.wrappers import register_wrapper

from .resource import KtbsResourceMixin
from ..namespace import KTBS
from ..utils import extend_api

@register_wrapper(KTBS.BuiltinMethod)
@extend_api
class MethodBuiltinMixin(KtbsResourceMixin):
    """
    I provide the pythonic interface common to kTBS methods.
    """

    ######## Abstract kTBS API ########

    def get_base(self):
        """A built-in method has no base.
        """
        # method could be a function #pylint: disable=R0201
        return None

    def get_parent(self):
        """A built-in method has no parent.
        """
        # method could be a function #pylint: disable=R0201
        return None

    def set_parent(self, parent):
        """A built-in method can have no parent.
        """
        # method could be a function #pylint: disable=R0201
        # unused argument #pylint: disable=W0613
        raise TypeError("A built-in method can have no parent")

    def list_parameters(self, include_inherited):
        """A built-in method has no parameter.
        """
        # method could be a function #pylint: disable=R0201
        # unused argument #pylint: disable=W0613
        return ()

    def get_parameter(self, key):
        """A built-in method has no parameters.
        """
        # method could be a function #pylint: disable=R0201
        # unused argument #pylint: disable=W0613
        return None

    def set_paremeter(self, key, value):
        """A built-in method can have no parameter.
        """
        # method could be a function #pylint: disable=R0201
        # unused argument #pylint: disable=W0613
        raise TypeError("A built-in method can have no parameter")

    def del_parameter(self, key):
        """A built-in method has no parameters.
        """
        # method could be a function #pylint: disable=R0201
        # unused argument #pylint: disable=W0613
        return None
