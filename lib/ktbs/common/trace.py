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
I provide the pythonic interface to traces (abstract and stored).
"""
from ktbs.common.base import InBaseMixin
from ktbs.common.utils import coerce_to_uri, extend_api
from ktbs.iso8601 import parse_date, ParseError
from ktbs.namespaces import KTBS

@extend_api
class TraceMixin(InBaseMixin):
    """
    I provide the pythonic interface common to all traces.
    """
    def iter_obsels(self, begin=None, end=None, desc=False):
        """
        Iter over the obsels of this trace.

        The obsel are sorted by their end timestamp, then their begin
        timestamp, then their identifier. If desc is true, the order is
        inversed.

        If given, begin and/or end are interpreted as the (included)
        boundaries of an interval; only obsels entirely contained in this
        interval will be yielded.

        * begin: an int, datetime or Obsel
        * end: an int, datetime or Obsel
        * desc: an object with a truth value

        NB: the order of "recent" obsels may vary even if the trace is not
        amended, since collectors are not bound to respect the order in begin
        timestamps and identifiers.
        """
        if begin or end or desc:
            raise NotImplementedError(
                "iter_obsels parameters not implemented yet")
            # TODO MAJOR implement parameters of iter_obsels
        make_resource = self.make_resource
        for obs in self.graph.subjects(_HAS_TRACE, self.uri):
            yield make_resource(obs)

    def get_obsel(self, uri):
        """
        Return the obsel with the given uri.

        `uri` may be relative to the URI of the trace.
        """
        uri = coerce_to_uri(uri, self.uri)
        return self.make_resource(uri)

    def get_model(self):
        """
        I return the trace model of this trace.
        """
        tmodel_uri = self.get_object(_HAS_MODEL)
        return self.make_resource(tmodel_uri)
        # TODO MAJOR make_resource return None for external models; fix this

    def get_origin(self):
        """
        I return the origin of this trace, as a python datetime or a str.

        Only if the origin can not be converted to a datetime is it returned
        as a str.
        """
        origin = self.get_object(_HAS_ORIGIN)
        try:
            return parse_date(origin)
        except ParseError:
            return origin

    def iter_sources(self):
        """
        I iter over the sources of this computed trace.
        """
        make_resource = self.make_resource
        for src in self.iter_objects(_HAS_SOURCE):
            yield make_resource(src)

    def iter_transformed_traces(self):
        """
        Iter over the traces having this trace as a source.
        """
        make_resource = self.make_resource
        for trc in self.iter_subjects(_HAS_SOURCE):
            yield make_resource(trc)


class StoredTraceMixin(TraceMixin):
    """
    I provide the pythonic interface to stored traces.
    """
    pass
    # TODO MAJOR implement part of the abstract API

_HAS_MODEL = KTBS.hasModel
_HAS_ORIGIN = KTBS.hasOrigin
_HAS_SOURCE = KTBS.hasSource
_HAS_TRACE = KTBS.hasTrace
