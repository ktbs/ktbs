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

"""I define the interface of a method implementation.
"""

class IMethod(object):
    """I define the interface of a method implementation.
    """

    def compute_trace_description(self, computed_trace):
        """I set the computed properties (model, origin) of the given trace

        :param computed_trace: a :class:`..engine.trace.ComputedTrace`

        :rtype: :class:`rdfrest.util.Diagnosis`

        The returned diagnosis must be non-empty if the model and/or the origin
        could not be set, or if it is predicatable that compute_obsels will
        fail. It can be non-empty in other situations, but the message should
        then make it clear that it is a mere warning (rather than an error).

        Note also that after this method is called, `compute_obsels`:meth: is
        expected to start afresh.
        """
        raise NotImplementedError

    def compute_obsels(self, computed_trace, from_scratch=False):
        """I update the obsels of the given computed trace

        :param computed_trace: a :class:`..engine.trace.ComputedTrace`
        :param from_scratch: force a complete recalculation,
                             regardless of the state of the sources

        :rtype: :class:`rdfrest.util.Diagnosis`

        """
        raise NotImplementedError
