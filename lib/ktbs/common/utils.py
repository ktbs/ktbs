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
I provide utility functions for pythonic interfaces.
"""
from rdflib import URIRef
import re
from urlparse import urljoin

def coerce_to_uri(obj, base=None):
    """
    I convert to URIRef an object that can be either a URIRef, an object with a
    'uri' attribute (assumed to be a URIRef) or a string-like URI.
    """
    ret = obj
    if not isinstance(ret, URIRef):
        ret = getattr(ret, "uri", None) or str(ret)
    if base is not None:
        ret = urljoin(base, ret)
    if not isinstance(ret, URIRef):
        ret = URIRef(ret)
    return ret

def extend_api(cls):
    """
    I extend cls according to the design rationale of the kTBS abstract API.

    More precisely:
    * for every get_x(...) method I add a 'x' property (if it accepts 0 args)
    * for every set_x(...) method I add a setter to the 'x' property
    * for every iter_xs(...) method I add a list_xs(...) method
    * for every iter_xs(...) method I add a 'xs' property (if it accepts 0 args)
    """
    methods = [ pair for pair in cls.__dict__.items()
                if _INTERESTING_METHOD.match(pair[0]) ]
    methods.sort()  # put all the get_ before the set_
    for methodname, raw_function in methods:
        nrequired = (raw_function.func_code.co_argcount
                     - len(raw_function.func_defaults or ()))
        if methodname.startswith("get_"):
            if nrequired > 1: # self is always required
                continue
            stripped_name = methodname[4:]
            prop = property(raw_function, doc=raw_function.__doc__)
            setattr(cls, stripped_name, prop)
        elif methodname.startswith("set_"):
            if nrequired > 2: # self is always required
                continue
            stripped_name = methodname[4:]
            prop = getattr(cls, stripped_name, None)
            if prop is None:
                prop = property(doc=raw_function.__doc__)
            setattr(cls, stripped_name, prop.setter(raw_function))
        else: # methodname.startswith("iter_"):
            stripped_name = methodname[5:]
            func = eval("lambda self, *args, **kw: list(self.%s(*args, **kw))"
                        % methodname) # eval is necessary:
            # calling raw_function from inside a lambda doesn't work
            func.func_name = "list_%s" % stripped_name
            func.__doc__ = "Make a list from %s" % methodname
            setattr(cls, func.func_name, func)

            if nrequired > 1: # self is always required
                continue
            prop = property(func, doc=func.__doc__)
            setattr(cls, stripped_name, prop)

    return cls

_INTERESTING_METHOD = re.compile("get_|set_|iter_")
