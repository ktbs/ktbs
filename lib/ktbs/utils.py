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
I provide utility functions for pythonic interfaces.
"""
from rdflib import Namespace, URIRef
import re

from rdfrest.exceptions import InvalidDataError
from rdfrest.util import coerce_to_uri, check_new, make_fresh_uri

# useful namespaces

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


def extend_api(cls):
    """
    I extend cls according to the design rationale of the kTBS abstract API.

    More precisely:
    * for every get_x(...) method I add a 'x' property (if it accepts 0 args)
    * for every set_x(...) method I add a setter to the 'x' property
    * for every iter_xs(...) method I add a list_xs(...) method
    * for every iter_xs(...) method I add a 'xs' property (if it accepts 0 args)
    """
    # Use of the exec statement #pylint: disable=W0122

    methods = [ pair for pair in cls.__dict__.items()
                if _INTERESTING_METHOD.match(pair[0]) ]
    methods.sort()  # put all the get_ before the set_
    for methodname, raw_function in methods:
        if hasattr(raw_function, "_extend_api_ignore"):
            continue
        if isinstance(raw_function, classmethod):
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
            new_name = "list_%s" % stripped_name
            repo = {}
            exec ("""def %(new_name)s(self, *args, **kw):
                         "Make a list from %(methodname)s"
                         return list(self.%(methodname)s(*args, **kw))
                  """ % locals()) in globals(), repo
            func = repo[new_name]
            setattr(cls, new_name, func)

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

def mint_uri_from_label(label, target, uri=None, suffix=""):
    """
    Mint a URI for a resource posted to `target` based on `label`.

    :param label:  the label for the resource to create
    :param target: the resource "containing" the resource to create
    :param uri:    if provided, will be used instead (must be fresh)
    :param suffix: if provided, will be added to the end of the URI

    :return: a URI not present in `target.state`
    :rtype: rdflib.URIRef
    :raise: InvalidDataError if `uri` is provided and not acceptable
    """
    if uri is not None:
        uri = coerce_to_uri(uri, target.uri)
        if not check_new(target.state, uri):
            raise InvalidDataError("URI already in use <%s>" % uri)
        if not uri.startswith(target.uri):
            raise InvalidDataError(
                "URI is wrong <%s> (did you forget a leading '#'?)" % uri)
    else:
        label = label.lower()
        prefix = target.uri
        if prefix[-1] != "/":
            prefix = "%s#" % prefix
        prefix = "%s%s" % (prefix, _NON_ALPHA.sub("-", label))
        uri = URIRef("%s%s" % (prefix, suffix))
        if not check_new(target.state, uri):
            prefix = "%s-" % prefix
            uri = make_fresh_uri(target.state, prefix, suffix)
    return uri
        
def short_name(uri):
    """
    Return the last part of the URI (fragment or path element).
    """
    hashpos = uri.rfind("#", 0, -1)
    slashpos = uri.rfind("/", 0, -1)
    return uri[max(hashpos, slashpos+1):]


_INTERESTING_METHOD = re.compile("get_|set_|iter_")
_NON_ALPHA = re.compile(r'[^\w]+')
