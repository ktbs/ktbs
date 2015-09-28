#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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

"""I provide functionalities to parse RDF-REST resource.

I act as a registry of parsers. Parsers can be
`iterated by decreasing preference <iter_parsers>`func:, selected based on
`content-type <get_parser_by_content_type>`:func: or
`extension <get_parser_by_extension>`:func:.

I provide a number of default parsers, but additional parsers can be
`added in the registry<register_parser>`:func:.
"""
from bisect import insort
from rdflib import BNode, Graph

from .exceptions import ParseError
from .util import coerce_to_uri, wrap_exceptions

################################################################
#
# Parser registration
#

def register_parser(content_type, extension=None, preference=80):
    """I return a decorator for registering a parser.
    
    The decorated function must have the same prototype as
    :func:`parse_rdf_xml`.
    
    :param content_type: a content-type as a str
    :param extension:    the file extension associated with this parser
    :param preference:   an int between 0 (low) and 100 (high)

    The decorated function must have the same prototype as
    :func:`parse_rdf_xml`, and should raise `~.exceptions.ParseError`
    when it fails to parse the given content.
    """
    def decorator(func):
        """The decorator to register a parser."""
        _PREGISTRY.register(func, content_type, extension, preference)
        return func
    return decorator

def iter_parsers():
    """Iter over all the parsers available for this rdf_type.

    :return: an iterator of tuples (parser_function, content_type, extension)

    Parsers are iterated in decreasing order of preference.
    """
    return iter(_PREGISTRY)

def get_parser_by_content_type(content_type):
    """I return the best parser associated with content_type, or None.

    :return: a tuple (parser_function, extension) or (None, None)
    """
    return _PREGISTRY.get_by_content_type(content_type)

def get_parser_by_extension(extension):
    """Return the parser associated with the best preference score.

    :return: a tuple (parser_function, content_type) or (None, None)
    """
    return _PREGISTRY.get_by_extension(extension)


class _FormatRegistry(object):
    """I provide functionalities for registering formats.

    This is used in modules `.serializers`:mod: and `.parsers`:mod:.
    """

    def __init__(self):
        self._by_pref = []
        self._by_ext = {}
        self._by_ctype = {}

    def register(self, formatfunc, content_type, extension, preference):
        """I register a format function in this registry.

        :param formatfunc:   the format function to register
        :param content_type: a content-type as a str
        :param extension:    the file extension associated with this format
        :param preference:   an int between 0 (low) and 100 (high)
        """
        assert 0 <= preference <= 100
        insort(self._by_pref,
               (100-preference, formatfunc, content_type, extension))
        _set_if_higher_pref(self._by_ctype, content_type,
                            (formatfunc, extension, preference))
        _set_if_higher_pref(self._by_ext, extension,
                            (formatfunc, content_type, preference))

    def __iter__(self):
        """Iter over registered formats in order of decreasing preference.

        :return: an iterator of tuples (function, content_type, extension)
        """
        return ( i[1:] for i in self._by_pref )

    def get_by_content_type(self, content_type):
        """I return the format function associated with content_type, or None.

        :return: a tuple (function, extension) or (None, None)
        """
        return self._by_ctype.get(content_type, (None, None, None))[:-1]

    def get_by_extension(self, extension):
        """I return the format function associated with extension, or None.

        :return: a tuple (function, content_type) or (None, None)
        """
        return self._by_ext.get(extension, (None, None, None))[:-1]

def _set_if_higher_pref(adict, key, val):
    """Set a val in FormatRegistry's dicts."""
    existing = adict.get(key)
    if existing is None or existing[-1] <= val[-1]:
        adict[key] = val

_PREGISTRY = _FormatRegistry()


################################################################
#
# Default parser implementations
#

@register_parser("application/rdf+xml")
def parse_rdf_xml(content, base_uri=None, encoding="utf-8", graph=None):
    """I parse RDF content from RDF/XML.

    :param content:  a byte string
    :param base_uri: the base URI of `content`
    :param encoding: the character encoding of `content`
    :param graph:    if provided, the graph to parse into

    :return: an RDF `~rdflib.Graph`:class:
    :raise: :class:`rdfrest.exceptions.ParseError`

    """
    return _parse_with_rdflib(content, base_uri, encoding, "xml", graph)

@register_parser("text/turtle")
@register_parser("text/n3",              20)
@register_parser("text/x-turtle",        20)
@register_parser("application/turtle",   20)
@register_parser("application/x-turtle", 20)
def parse_turtle(content, base_uri=None, encoding="utf-8", graph=None):
    """I parse RDF content from Turtle.

    See `parse_rdf_xml` for prototype documentation.
    """
    return _parse_with_rdflib(content, base_uri, encoding, "n3", graph)

@register_parser("text/nt",    40)
@register_parser("text/plain", 20)
def parse_ntriples(content, base_uri=None, encoding="utf-8", graph=None):
    """I parse RDF content from N-Triples.

    See `parse_rdf_xml` for prototype documentation.
    """
    return _parse_with_rdflib(content, base_uri, encoding, "nt", graph)


@wrap_exceptions(ParseError)
def _parse_with_rdflib(content, base_uri, encoding, rdflib_format, graph):
    "Common implementation of all rdflib-based parse functions."
    if graph is None:
        if base_uri is None:
            identifier = BNode()
        else:
            identifier = coerce_to_uri(base_uri)
        graph = Graph(identifier=identifier)
    if encoding.lower() != "utf-8":
        content = content.decode(encoding).encode("utf-8")
    graph.parse(data=content, publicID=base_uri, format=rdflib_format)
    return graph

