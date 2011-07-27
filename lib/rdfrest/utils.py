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
from functools import wraps
from random import choice
from rdflib import BNode, URIRef

def cache_result(callabl):
    """Decorator for caching the result of a callable.

    It is assumed that `callabl` only has a `self` parameter, and always
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

def check_new(graph, node):
    """Check that node is absent from graph.
    """
    if next(graph.predicate_objects(node), None) is not None:
        return False
    if next(graph.subject_predicates(node), None) is not None:
        return False
    return True

def coerce_to_uri(obj, base=None):
    """I convert `obj` to a URIRef.
    
    :param obj:  either an `rdflib.URIRef`, an object with a `uri` attribute
                 (assumed to be a URIRef) or a string-like URI.
    :param base: if provided, a string-like absolute URI used to resolve `obj`
                 if it is itself a string.

    :rtype: rdflib.URIRef
    """
    assert obj is not None
    ret = obj
    if not isinstance(ret, URIRef):
        ret = getattr(ret, "uri", None) or str(ret)
    if not isinstance(ret, URIRef):
        ret = URIRef(ret, base)
    return ret

def coerce_to_node(obj, base=None):
    """I do the same as :func:`coerce_to_uri` above, but in addition:

    * if `obj` is None, I will return a fresh BNode
    * if `obj` is a BNode, I will return it
    """
    if obj is None:
        return BNode()
    elif isinstance(obj, BNode):
        return obj
    else:
        return coerce_to_uri(obj, base)

def extsplit(path_info):
    """Split a URI path into the extension-less path and the extension.
    """
    dot = path_info.rfind(".")
    slash = path_info.rfind("/")
    if dot < slash:
        return path_info, None
    else:
        return path_info[:dot], path_info[dot+1:]
    #

def make_fresh_uri(graph, prefix, suffix=""):
    """Creates a URIRef which is not in graph, with given prefix and suffix.
    """
    length = 2
    while True:
        node = URIRef("%s%s%s" % (prefix, random_token(length), suffix))
        if check_new(graph, node):
            return node
        length += 1

def random_token(length, characters="abcdefghijklmnopqrstuvwxyz0123456789"):
    """Create a random opaque string.

    :param length:     the length of the string to generate
    :param characters: the range of characters to use
    """
    return "".join( choice(characters) for i in range(length) )
