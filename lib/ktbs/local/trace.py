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
I provide the local implementation of ktbs:StoredTrace and ktbs:ComputedTrace .
"""
from datetime import datetime, timedelta

from rdflib import Literal
from rdfrest.mixins import RdfPostMixin

from ktbs.common.trace import StoredTraceMixin
from ktbs.common.utils import extend_api
from ktbs.iso8601 import parse_date
from ktbs.local.base import BaseResource
from ktbs.namespaces import KTBS

@extend_api
class StoredTrace(StoredTraceMixin, RdfPostMixin, BaseResource):
    """
    I provide the pythonic interface common to ktbs stored trace.
    """

    # KTBS API #

    # TODO

    # RDF-REST API #

    RDF_MAIN_TYPE = KTBS.StoredTrace

    RDF_PUTABLE_OUT = [ KTBS.hasModel, KTBS.hasOrigin, KTBS.hasTraceBegin,
                        KTBS.hasTraceEnd, KTBS.hasTraceBeginDT,
                        KTBS.hasTraceEndDT, ]
    RDF_CARDINALITY_OUT = [
        (KTBS.hasModel, 1, 1),
        (KTBS.hasOrigin, 1, 1),
        (KTBS.hasTraceBegin, None, 1),
        (KTBS.hasTraceBeginDT, None, 1),
        (KTBS.hasTraceEnd, None, 1),
        (KTBS.hasTraceEndDT, None, 1),
        ]
    
    @classmethod
    def check_new_graph(cls, uri, new_graph, resource=None, added=None,
                        removed=None):
        """I override `rdfrest.mixins.RdfPostMixin.check_new_graph`.
        """

        # TODO check that method is from the same base
        #  generalize _check_parent_method in base, and make it public
        # TODO check trace time bounds, if any
        #  pb: the function below assumes they are both present, fix this

        # just checking their syntax for the moment
        errors = super(StoredTrace, cls).check_new_graph(
            uri, new_graph, resource, added, removed) or []

        if added:
            # we only check values that were added/changed
            the_graph = added
        else:
            the_graph = new_graph

        # TODO check things
        uri_base = uri[:uri[:-1].rfind("/")+1]
        print the_graph, uri_base

        if errors:
            return "\n".join(errors)
        else:
            return None
        

    def find_created(self, new_graph, query=None):
        """I override `rdfrest.mixins.RdfPostMixin.find_created`.

        I only search for nodes that have ktbs:hasTrace this trace.
        """
        if query is None:
            query = "SELECT ?c WHERE { ?c <%s> <%%(uri)s> }" % _HAS_TRACE
        return super(StoredTrace, self).find_created(new_graph, query)

    def get_created_class(self, rdf_type):
        """I override `rdfrest.mixins.RdfPostMixin.get_created_class`.

        I return Obsel regardless of the type, because Obsels do not have
        explicitly the type ktbs:Obsel.
        """
        return Obsel


def timedelta_in_ms(delta):
    """Compute the number of milliseconds in a timedelta.
    """
    return (delta.microseconds / 1000 +
            (delta.seconds + delta.days * 24 * 3600) * 1000)

def sanitize_temporal_boundaries(begin_il, end_il, begin_dl, end_dl, origin):
    """Check that arguments are consistent, and fill in missing values.

    Consistent means:
    * if origin is opaque, begin_d and end_d are None
    * else, begin_i and begin_d (resp. end_i and end_d), if they are both
      provided,  must represent the same point in time.

    :param begin_i: the begin timestamp in ms since origin, or None
    :type  begin_i: Literal with datatype xsd:integer
    :param end_i: the end timestamp in ms since origin, or None
    :type  end_i: Literal with datatype xsd:integer
    :param begin_d: the begin timestamp in calendar time, or None
    :type  begin_d: Literal with datatype xsd:datetime
    :param end_d: the end timestamp in calendar time, or None
    :type  end_d: Literal with datatype xsd:datetime
    :param origin: the origin of the trace
    :type  origin: datetime or str

    :return: new values, as literal, a list of tuples (predicate, value) to add to the model.

    Pre-condition: begin_i and begin_d (resp. end_i and end_d) can not be both
    None.

    NB: if origin is opaque, None is returned for begin_d and end_d
    """
    if not isinstance(origin, datetime):
        if begin_dl or end_dl:
            raise ValueError("Can not use absolute timestamp with opaque "
                             "origin")
        else:
            return begin_il, end_il, None, None

    if begin_il is not None:
        begin_i = begin_il.toPython()
        assert isinstance(begin_i, int), repr(begin_i)
    else:
        begin_i = None
    if end_il is not None:
        end_i = end_il.toPython()
        assert isinstance(end_i, int), repr(end_i)
    else:
        end_i = None
    if begin_dl is not None:
        begin_d = parse_date(begin_dl)
        assert isinstance(begin_d, datetime), repr(begin_d)
    else:
        begin_d = None
    if end_dl is not None:
        end_d = parse_date(end_dl)
        assert isinstance(end_d, datetime), repr(end_d)
    else:
        end_d = None

    if begin_i is None: # then begin_d is not None
        # TODO MINOR below, should rather use the unit of the *model*
        begin_i = timedelta_in_ms(begin_d - origin)
        begin_il = Literal(begin_i)
    elif begin_d is None: # then begin_i is not None
        # TODO MINOR below, should rather use the unit of the *model*
        begin_dl = Literal(origin + timedelta(milliseconds=begin_i))
    else: # both are not None, so check consistency
        # TODO MINOR below, should rather use the unit of the *model*
        begin_di = timedelta_in_ms(begin_d - origin)
        if begin_i != begin_di:
            raise ValueError("Inconsistent begin timestamps")

    if end_i is None:
        # TODO MINOR below, should rather use the unit of the *model*
        end_i = timedelta_in_ms(end_d - origin)
        end_il = Literal(end_i)
    elif end_d is None:
        # TODO MINOR below, should rather use the unit of the *model*
        end_dl = Literal(origin + timedelta(milliseconds=end_i))
    else: # both can not be None, so check consistency
        # TODO MINOR below, should rather use the unit of the *model*
        end_di = timedelta_in_ms(end_d - origin)
        if end_i != end_di:
            raise ValueError("Inconsistent end timestamps")

    if begin_i > end_i:
        raise ValueError("begin (%s) is after end (%s)" % (begin_i, end_i))

    return begin_il, end_il, begin_dl, end_dl
    
# import Obsel in the end, as it is logically "below" trace
from ktbs.local.obsel import Obsel

_HAS_TRACE = KTBS.hasTrace
