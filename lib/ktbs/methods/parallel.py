#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
Implementation of the parallel builtin methods.
"""
from rdfrest.utils import Diagnosis

from rdflib import URIRef

from .interface import IMethod
from ..namespace import KTBS
from ..engine.builtin_method import register_builtin_method_impl

class _ParallelMethod(IMethod):
    """I implement the parallel builtin method.
    """
    uri = KTBS.parallel

    def compute_trace_description(self, computed_trace):
        """I implement :meth:`.interface.IMethod.compute_trace_description`.
        """
        diag = Diagnosis("parallel.compute_trace_description")
        diag.append("Not implemented yet")
        return diag

    def compute_obsels(self, computed_trace):
        """I implement :meth:`.interface.IMethod.compute_obsels`.
        """
        diag = Diagnosis("parallel.compute_obsels")
        diag.append("Not implemented yet")
        return diag

register_builtin_method_impl(_ParallelMethod())

# TODO LATER remove this, as this is a deprecated feature
# alias ktbs:parallel as ktbs:supermethod (old name)
_SUPERMETHOD = _ParallelMethod()
_SUPERMETHOD.uri = URIRef("%ssupermethod" % KTBS)
register_builtin_method_impl(_SUPERMETHOD)
# dummy ktbs:script-python method, not supported anymore anyway
# so it does not matter which actual method we put there
_SCRIPTPYTHON = _ParallelMethod()
_SCRIPTPYTHON.uri = URIRef("%sscript-python" % KTBS)
register_builtin_method_impl(_SCRIPTPYTHON)
