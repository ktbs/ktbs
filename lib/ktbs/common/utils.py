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
from httplib2 import Http
from rdflib import URIRef
import re

from rdfrest.utils import coerce_to_uri, check_new, make_fresh_uri

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
        if hasattr(raw_function, "_extend_api_ignore"):
            continue
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

def extend_api_ignore(func):
    """I decorate functions that must be ignored by :func:`extend_api`.
    """
    func._extend_api_ignore = True
    return func

def mint_uri(label, target, uri=None):
    """
    Mint a URI for a resource posted to `target` based on `label`.

    :param label:  the label for the resource to create
    :param target: the resource "containing" the resource to create
    :param uri:    if provided, wil be used instead (must be fresh)

    :return: a URI not present in `target.graph`
    :rtype: rdflib.URIRef
    :raise: ValueError if `uri` is provided and is already in use
    """
    target_graph = target._graph # protected member #pylint: disable=W0212
    if uri is not None:
        uri = coerce_to_uri(uri, target.uri)
        if not check_new(target_graph, uri):
            raise ValueError("URI already in use <%s>" % uri)
    else:
        prefix = target.uri
        if prefix[-1] != "/":
            prefix = "%s#" % prefix
        uri = URIRef("%s%s" % (prefix, _NON_ALPHA.sub(label, "-")))
        if not check_new(target_graph, uri):
            prefix = "%s-" % uri
            uri = make_fresh_uri(target_graph, prefix)
    return uri
        

def short_name(uri):
    """
    Return the last part of the URI (fragment of path element).
    """
    hashpos = uri.rfind("#", 0, -1)
    slashpos = uri.rfind("/", 0, -1)
    return uri[max(hashpos, slashpos)+1:]

def post_graph(graph, uri, rdflib_format="n3"):
    """
    I post the given graph to the given URI, and raise an exception on error.
    """
    data = graph.serialize(format=rdflib_format)
    headers = {
        'content-type': 'text/turtle',
        }
    rheaders, rcontent = Http().request(uri, 'POST', data, headers=headers)
    if rheaders.status / 100 != 2:
        raise ValueError(rheaders, rcontent) # TODO make a better exception
    
    return rheaders, rcontent

_INTERESTING_METHOD = re.compile("get_|set_|iter_")
_NON_ALPHA = re.compile(r'[^\w]+')
