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
I provide the client implementation of Method
"""
from ktbs.client.resource import Resource
from ktbs.common.method import MethodMixin
from ktbs.namespaces import KTBS


class Method(MethodMixin, Resource):
    """TODO docstring"""
    # TODO implement client-specifid methods

    RDF_MAIN_TYPE = KTBS.Method

class BuiltinMethod(object):
    """Dummy class used for instantiating built-in methods.
    """
    # too few public method #pylint: disable=R0903
    RDF_MAIN_TYPE = KTBS.BuiltinMethod

    def __init__(self, uri, graph=None):
        """Initialize Resource common subclass.

        :param uri: Absolute or relative URI.
        :param graph: At the moment there's no graph returned for builtin 
        methods.
        pylint: disable-msg=W0231
        """
        self.uri = uri
        self.__graph = graph # fake to get rid of pylint W0613 Unused argument

    def get_uri(self):
        """
        Return the URI of this resource.
        """
        # Similar lines in 2 files #pylint: disable-msg=R0801
        return self.uri
