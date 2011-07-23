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
I provide functionalities to register a number of parsers with
preference levels and associated content-types.

There is a default register from which any specific register inherits.
"""
from bisect import insort
from rdflib import Graph

from rdfrest.exceptions import ParseError

class ParserRegister(object):
    """I provide functionalities for registering parsers.
    """

    __default = None

    @classmethod
    def get_default(cls):
        """I retun the default parser register.
        """
        if ParserRegister.__default is None:
            ParserRegister.__default = ParserRegister()
        return ParserRegister.__default

    def __init__(self):
        default = ParserRegister.__default
        if default is None: # self will become default
            self._by_pref = []
            self._by_ctype = {}
        else:
            # access to protected member:
            self._by_pref = list(default._by_pref)   #pylint: disable=W0212
            self._by_ctype = dict(default._by_ctype) #pylint: disable=W0212

    def register(self, content_type, preference=80):
        """I return a decorator for registering a parser.

        The decorated function must have the same prototype as
        :func:`parse_rdf_xml`.

        :param content_type: a content-type as a str
        :param preference:   an int between 0 (low) and 100 (high)
        """
        assert 0 <= preference <= 100
        assert content_type not in self._by_ctype, \
            "%s parser registered twice" % content_type
        def the_decorator(func):
            "Register `func` as a parser"
            insort(self._by_pref, (100-preference, func, content_type))
            self._by_ctype[content_type] = func
            return func
        return the_decorator
        
    def __iter__(self):
        """Iter over registered parsers in order of decreasing preference.

        :return: an iterator of functions
        """
        return ( i[1:] for i in self._by_pref )

    def get_by_content_type(self, content_type):
        """I return the parser associated with content_type, or None.

        :return: a function
        """
        return self._by_ctype.get(content_type)


def register(content_type, preference=80):
    """Shortcut to 
    :meth:`ParserRegister.register ParserRegister.get_default().register`
    """
    return ParserRegister.get_default().register(content_type, preference)


@register("application/rdf+xml")
def parse_rdf_xml(content, base_uri=None, encoding="utf-8"):
    """I parse RDF content from RDF/XML.

    :param content:  a byte string
    :param base_uri: the base URI of `content`
    :param encoding: the character encoding of `content`

    :return: an RDF graph
    :rtype:  rdflib.Graph
    :raise: :class:`rdfrest.exceptions.ParseError`

    """
    return _parse_with_rdflib(content, base_uri, encoding, "xml")

@register("text/turtle")
@register("text/n3",              20)
@register("text/x-turtle",        20)
@register("application/turtle",   20)
@register("application/x-turtle", 20)
def parse_turtle(content, base_uri=None, encoding="utf-8"):
    """I parse RDF content from Turtle.

    See `parse_rdf_xml` for prototype documentation.
    """
    return _parse_with_rdflib(content, base_uri, encoding, "n3")

@register("text/nt",    40)
@register("text/plain", 20)
def parse_ntriples(content, base_uri=None, encoding="utf-8"):
    """I parse RDF content from N-Triples.

    See `parse_rdf_xml` for prototype documentation.
    """
    return _parse_with_rdflib(content, base_uri, encoding, "nt")


def _parse_with_rdflib(content, base_uri, encoding, rdflib_format):
    "Common implementation of all rdflib-based parse functions."
    graph = Graph()
    if encoding.lower() != "utf-8":
        content = content.decode(encoding).encode("utf-8")
    try:
        graph.parse(data=content, publicID=base_uri, format=rdflib_format)
    except Exception, ex:
        raise ParseError(ex.message or str(ex), ex)
    return graph

