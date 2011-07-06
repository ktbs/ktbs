#    This file is part of RDF-REST <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    RDF-REST is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RDF-REST is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with RDF-REST.  If not, see <http://www.gnu.org/licenses/>.

"""
I define useful functions and classes for RDF RESTful services.
"""
from datetime import datetime
from functools import wraps
from md5 import md5
from rdflib import URIRef

def cache_result(callabl):
    """
    Decorator for caching the result of a callable.

    It is assumed that callable only has a `self` parameter, and always
    returns the same value.
    """
    cache_name = "__cache_%s" % callabl.__name__
    
    @wraps(callabl)
    def wrapper(self):
        "the decorated callable"
        ret = getattr(self, cache_name, None)
        if not hasattr(self, cache_name):
            ret = callabl(self)
            setattr(self, cache_name, ret)
        else:
            ret = getattr(self, cache_name)
        return ret
    return wrapper

def check_new(model, node):
    """
    Check that node is absent from model (in the given context, if any).
    """
    res = model.query("ASK { <%s> ?p ?o }" % node)
    if res.askAnswer[0]:
        return False
    res = model.query("ASK { ?s ?p <%s> }" % node)
    if res.askAnswer[0]:
        return False
    return True

def extsplit(path_info):
    """
    Split a URI path into the extension-less path and the extension.
    """
    dot = path_info.rfind(".")
    slash = path_info.rfind("/")
    if dot < slash:
        return path_info, None
    else:
        return path_info[:dot], path_info[dot+1:]
    #

def make_fresh_resource(model, prefix, suffix=""):
    """
    Creates a URI Node which is not in model, with given prefix and suffix.
    """
    length = 3
    while True:
        token = md5(prefix + _NOW().isoformat()).hexdigest()[:length]
        node = URIRef("%s%s%s" % (prefix, token, suffix))
        if check_new(model, node):
            return node
        length += 1

_NOW = datetime.now
