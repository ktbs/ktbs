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
from rdflib import Literal

from ktbs.common.base import InBaseMixin
from ktbs.common.utils import extend_api
from ktbs.iso8601 import parse_date
from ktbs.namespaces import KTBS
from rdfrest.utils import coerce_to_uri

@extend_api
class TraceMixin(InBaseMixin):
    """
    I provide the pythonic interface common to all traces.
    """
    def get_obsel(self, id):
        """
        Return the obsel with the given uri.

        `uri` may be relative to the URI of the trace.
        """
        #pylint: disable-msg=W0622
        #  Redefining built-in id
        uri = coerce_to_uri(id, self.uri)
        return self.make_resource(uri, KTBS.Obsel)

    def get_model(self):
        """
        I return the trace model of this trace.
        """
        tmodel_uri = self._graph.value(self.uri, _HAS_MODEL)
        return self.make_resource(tmodel_uri)
        # TODO MAJOR make_resource return None for external models; fix this

    def get_origin(self, as_datetime=False):
        """
        I return the origin of this trace.

        If `as_datetime` is true, get_origin will try to convert the return
        value to datetime, or raise an exception on a failure.

        """
        origin = self._graph.value(self.uri, _HAS_TRACE_ORIGIN)
        if as_datetime:
            return parse_date(origin)
        else:
            return origin

    def iter_source_traces(self):
        """
        I iter over the sources of this computed trace.
        """
        make_resource = self.make_resource
        for src in self._graph.objects(self.uri, _HAS_SOURCE_TRACE):
            yield make_resource(src)

    def iter_transformed_traces(self):
        """
        Iter over the traces having this trace as a source.
        """
        make_resource = self.make_resource
        for trc in self._graph.subjects(self.uri, _HAS_SOURCE_TRACE):
            yield make_resource(trc)


@extend_api
class StoredTraceMixin(TraceMixin):
    """
    I provide the pythonic interface to stored traces.
    """
    def set_model(self, model):
        """I set the model of this trace.
        model can be a Model or a URI; relative URIs are resolved against this
        trace's URI.
        """
        model_uri = coerce_to_uri(model, self.uri)
        with self._edit as graph:
            graph.set((self.uri, _HAS_MODEL, model_uri))

    def set_origin(self, origin):
        """I set the origin of this trace.
        origin can be a string or a datetime.
        """
        isoformat = getattr(origin, "isoformat", None)
        if isoformat is not None:
            origin = isoformat()
        origin = Literal(origin)
        with self._edit as graph:
            graph.set((self.uri, _HAS_TRACE_ORIGIN, origin))

    def get_default_subject(self):
        """
        I return the default subject of this trace.
        """
        return self._graph.value(self.uri, _HAS_DEFAULT_SUBJECT)

    def set_default_subject(self, subject):
        """I set the default subject of this trace.
        """
        subject = Literal(subject)
        with self._edit as graph:
            graph.set((self.uri, _HAS_DEFAULT_SUBJECT, subject))


    # TODO MAJOR implement part of the abstract API


_HAS_DEFAULT_SUBJECT = KTBS.hasDefaultSubject
_HAS_MODEL = KTBS.hasModel
_HAS_TRACE_ORIGIN = KTBS.hasOrigin # should be renamed one day?
_HAS_SOURCE_TRACE = KTBS.hasSource # should be renamed one day?
_HAS_TRACE = KTBS.hasTrace
