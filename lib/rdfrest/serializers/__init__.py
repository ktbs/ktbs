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

"""I provide functionalities to serialize RDF-REST resource.

I act as a registry of serializers. Serializers can be
`iterated by decreasing preference <iter_serializers>`func:, selected based on
`content-type <get_serializer_by_content_type>`:func: or
`extension <get_serializer_by_extension>`:func:, and dedicated serializers can
be registered for a given RDF type.

I provide a number of default serializers, but additional serializers can be
`added in the registry<register_serializer>`:func:.

Finally, a numer of default `namespace prefixes <bind_prefix>`:func` can be set.
They will be shared with all registered serializers (but some third-party
serializers may not honnor them).
"""
from rdflib import Graph, RDF, RDFS, URIRef
from rdflib.plugins.serializers.nt import _nt_row

from ..exceptions import SerializeError
from ..parsers import _FormatRegistry
from ..util import coerce_to_uri, wrap_generator_exceptions
from .html import REST_CONSOLE


################################################################
#
# Serializer registration
#

_SREGISRIES = { None: _FormatRegistry() }
_NAMESPACES = {
    "rdf":     unicode(RDF),
    "rdfs":    unicode(RDFS),
    }

def register_serializer(content_type, extension=None, preference=80,
                        rdf_type=None):
    """I return a decorator for registering a serializer.
    
    The decorated function must have the same prototype as
    :func:`serialize_rdf_xml`.
    
    :param content_type: a content-type as a str
    :param extension:    the file extension associated with this serializer
    :param preference:   an int between 0 (low) and 100 (high)
    :param rdf_type:     if provided, the RDF type to which this serializer
                         applies

    The decorated function must have the same prototype as
    :func:`serialize_rdf_xml`, and should raise `~.exceptions.SerializeError`
    when it fails to serialize the given graph.
    """
    if rdf_type is not None:
        rdf_type = unicode(rdf_type)
    registry = _SREGISRIES.get(rdf_type)
    if registry is None:
        registry = _FormatRegistry()
        _SREGISRIES[rdf_type] = registry

    def decorator(func):
        """The decorator to register a serializer."""
        registry.register(func, content_type, extension, preference)
        return func
    return decorator

def iter_serializers(rdf_type=None):
    """Iter over all the serializers available for this rdf_type.

    :return: an iterator of tuples (serializer_function, contenttype, extension)

    Serializers are iterated in decreasing order of preference. Note that,
    if `rdf_type` is provided, a serializer associated with this type will
    always be preferred over a generic serializer (*i.e.* associated with no
    type), regardless of the preference score.
    """
    if rdf_type is not None:
        rdf_type = unicode(rdf_type)
        reg = _SREGISRIES.get(rdf_type)
        if reg:
            for i in reg:
                yield i
    for i in _SREGISRIES[None]:
        yield i

def get_serializer_by_content_type(content_type, rdf_type=None):
    """I return the best serializer associated with content_type, or None.

    :return: a tuple (serializer_function, extension) or (None, None)
    """
    if rdf_type is not None:
        rdf_type = unicode(rdf_type)
        reg = _SREGISRIES.get(rdf_type)
        if reg:
            ret = reg.get_by_content_type(content_type)
            if ret[0] is not None:
                return ret
    return _SREGISRIES[None].get_by_content_type(content_type)

def get_serializer_by_extension(extension, rdf_type=None):
    """Return the serializer associated with the best preference score.

    :return: a tuple (serializer_function, content_type) or (None, None)
    """
    if rdf_type is not None:
        rdf_type = unicode(rdf_type)
        reg = _SREGISRIES.get(rdf_type)
        if reg:
            ret = reg.get_by_extension(extension)
            if ret[0] is not None:
                return ret
    return _SREGISRIES[None].get_by_extension(extension)

def bind_prefix(prefix, namespace_uri):
    """I associate a namespace with a prefix for all registered serializers.
    """
    _NAMESPACES[prefix] = unicode(namespace_uri)

def get_prefix_bindings():
    """I return a fresh dict containing all the prefix bindings.

    :see also: :func:`bind_prefix`
    """
    return dict(_NAMESPACES)


################################################################
#
# Default serializer implementations
#

@register_serializer("application/rdf+xml", "rdf", 60)
@register_serializer("application/xml",     "xml", 20)
def serialize_rdf_xml(graph, resource, bindings=None):
    """I serialize an RDF graph as RDF/XML.

    :param graph:    the `~rdflib.Graph`:class: to serialize
    :param resource: the resource described by `graph` (its URI will used as
                     base URI)
    :param binding: a dict containing system-wide prefix bindings (defaults to
                    `get_prefix_bindings`:func:())

    :return: an iterable of UTF-8 encoded byte strings
    :raise: :class:`.exceptions.SerializeError` if the serializer can
            not serialize the given graph.

    .. important::

        Serializers that may raise a
        :class:`~rdfrest.exceptions.SerializeError` must *not* be implemented
        as generators, or the exception will be raised too late (i.e. when the
        `HttpFrontend` tries to send the response.
    """
    if False: # TODO LATER actually perform some checking
        raise SerializeError("RDF/XML can not encode this graph")
    bindings = bindings or dict(_NAMESPACES)
    return _serialize_with_rdflib("xml", graph, bindings, resource.uri)

@register_serializer("text/turtle",          "ttl")
@register_serializer("text/n3",              "n3",  20)
@register_serializer("text/x-turtle",        None,   20)
@register_serializer("application/turtle",   None,   20)
@register_serializer("application/x-turtle", None,   20)
def serialize_turtle(graph, uri, bindings=None):
    """I serialize an RDF graph as Turtle.

    See `serialize_rdf_xml` for prototype documentation.
    """
    bindings = bindings or dict(_NAMESPACES)
    return _serialize_with_rdflib("n3", graph, bindings, uri)

@wrap_generator_exceptions(SerializeError)
def _serialize_with_rdflib(rdflib_format, graph, bindings, base_uri):
    "Common implementation of all rdflib-based serialize functions."
    assert isinstance(rdflib_format, str)
    assert isinstance(graph, Graph)
    # copy in another graph to prevent polluting the original graph namespaces
    # TODO LATER find an efficient way to serialize a graph with custom NSs
    ser = Graph()
    ser_add = ser.add
    for triple in graph:
        ser_add(triple)
    for prefix, nsuri in bindings.items():
        ser.bind(prefix, nsuri)
    if base_uri is not None and not isinstance(base_uri, URIRef):
        base_uri = coerce_to_uri(base_uri)
    # We use yield to prevent the serialization to happen if a 304 is returned
    yield ser.serialize(None, format=rdflib_format, base=base_uri)

@register_serializer("text/nt",    "nt",  40)
@register_serializer("text/plain", "txt", 20)
@wrap_generator_exceptions(SerializeError)
def serialize_ntriples(graph, uri, bindings=None):
    """I serialize an RDF graph as N-Triples.

    See `serialize_rdf_xml` for prototype documentation.
    """
    # 'binding' and 'uri' not used #pylint: disable=W0613
    # NB: we N-Triples needs no base_uri or namespace management.
    # Also, we re-implement our own NT serializer in order to yield each triple
    # individually; this allows WSGI host to send chuncked content.

    # We use yield to prevent the serialization to happen if a 304 is returned
    for triple in graph:
        yield _nt_row(triple).encode("ascii", "replace")

@register_serializer("text/html", "html", 60)
@wrap_generator_exceptions(SerializeError)
def serialize_html(graph, resource, bindings=None):
    """I return a JS based REST console,
       that will then load the graph from the default serializer.
    """
    yield REST_CONSOLE
