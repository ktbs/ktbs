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

"""I implement a built-in method registry.
"""
from rdfrest.util import Diagnosis

from ..methods.interface import IMethod


_BUILTIN_METHODS = {}

def iter_builtin_method_impl():
    """I return an iterable of all supported built-in methods.
    """
    for i in _BUILTIN_METHODS.values():
        yield i

def register_builtin_method_impl(implementation):
    """I register the implementation of a builtin method.
    """
    uri = str(implementation.uri)
    _BUILTIN_METHODS[uri] = implementation

def get_builtin_method_impl(uri, _return_fake=False):
    """I return the implementation of a given built-in method.

    If no such implementation is found, I return None, unless `return_fake` is
    True; in the latter case, I return a fake implementation object that will
    fail to perform any computation.
    """
    ret = _BUILTIN_METHODS.get(str(uri))
    if ret is None and _return_fake:
        ret = _FakeMethod(str(uri))
    return ret


class _FakeMethod(IMethod):
    """I mimic IMethod when no matching method is found.
    """

    def __init__(self, uri):
        # IMethod.__init__ is not called #pylint: disable=W0231
        self.uri = uri
        self.diag = Diagnosis("_FakeMethod")
        self.diag.append("%s is not implemented; can not compute trace" % uri)

    def compute_trace_description(self, computed_trace):
        """I implement
        :meth:`..method.interface.IMethod.compute_trace_description`.
        """
        return self.diag

    def compute_obsels(self, computed_trace, from_scratch=False):
        """I implement :meth:`..method.interface.IMethod.compute_obsels`.
        """
        return self.diag


# ensure BuiltinMethodMixin is registeted,
import ktbs.api.builtin_method # unused import #pylint: disable=W0611

# ensure that all shipped built-in method implementations are registered
import ktbs.methods.filter    # reimport(?) #pylint: disable=W0404
import ktbs.methods.fusion   # reimport(?) #pylint: disable=W0404
import ktbs.methods.sparql   # reimport(?) #pylint: disable=W0404
import ktbs.methods.external   # reimport(?) #pylint: disable=W0404
