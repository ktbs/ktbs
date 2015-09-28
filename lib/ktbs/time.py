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

"""I provide time management for kTBS.

I provide a mechanism for registering time units.
"""

from rdflib import URIRef

from datetime import timedelta
from rdfrest.util.iso8601 import parse_date, ParseError
from .namespace import KTBS


def register_unit(uri, unit2timedelta, timedelta2unit):
    """I register converter functions for a unit URI.

    TODO DOC document signature and semantics of converter functions
    """
    assert isinstance(uri, URIRef)
    assert callable(unit2timedelta) and callable(timedelta2unit)
    assert uri not in _REGISTRY
    _REGISTRY[uri] = (unit2timedelta, timedelta2unit)

def get_converter_from_unit(uri):
    """I return a converter function from the given unit to `timedelta`.
    """
    assert isinstance(uri, URIRef)
    ret, _ = _REGISTRY.get(uri, (None, None))
    return ret

def get_converter_to_unit(uri):
    """I return a converter function from `timedelta` to the given unit.
    """
    assert isinstance(uri, URIRef)
    _, ret = _REGISTRY.get(uri, (None, None))
    return ret

_REGISTRY = {}

################################################################
#
# built-in time units
#

def ms2timedelta(a_int):
    """I convert from milliseconds to timedelta
    """
    return timedelta(0, 0, 0, a_int)

def timedelta2ms(a_timedelta):
    """I convert from timedelta to milliseconds
    """
    return int(round(a_timedelta.total_seconds() * 1000))

register_unit(KTBS.millisecond, ms2timedelta, timedelta2ms)

def sec2timedelta(a_int):
    """I convert from seconds to timedelta
    """
    return timedelta(0, a_int)

def timedelta2sec(a_timedelta):
    """I convert from timedelta to seconds
    """
    return int(round(a_timedelta.total_seconds()))

register_unit(KTBS.second, sec2timedelta, timedelta2sec)

################################################################
#
# helper functions
#

def lit2datetime(literal):
    """Convert `literal` to datetime if possible, else return None.

    If literal is None, also return None.
    """
    if literal is not None:
        try:
            return parse_date(literal)
        except ParseError:
            pass
    return None
