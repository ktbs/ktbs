"""
Serializers and Parsers for kTBS
"""

from rdflib import RDF
from rdfrest.parsers import wrap_exceptions
from rdfrest.serializers import get_prefix_bindings, iter_serializers, \
    register_serializer, SerializeError
from rdfrest.serializers_html import serialize_htmlized_turtle, \
    generate_htmlized_turtle

from ..namespace import KTBS

## HTML for obsel collections

def generate_obsels(graph, resource, bindings, ctypes):
    """
    I generate HTMLized Turtle for obsels (ordered by begin).
    """
    return generate_htmlized_turtle(graph, resource, bindings, ctypes, """
        SELECT ?s ?p ?o
        WHERE {
            ?s ?p ?o
            OPTIONAL { ?s <%s> ?begin }
        }
        ORDER BY DESC(?begin) ?s ?p ?o
                                    """ % (KTBS.hasBegin,))


@register_serializer("text/html", "html", 81, KTBS.ComputedTraceObsels)
@register_serializer("text/html", "html", 81, KTBS.StoredTraceObsels)
@wrap_exceptions(SerializeError)
def serialize_html(graph, resource, bindings=None):
    """Wiki rendering"""
    if bindings is None:
        bindings = get_prefix_bindings()
        for prefix in ( "", "m", "model"):
            if prefix not in bindings:
                bindings[prefix] = resource.trace.model_uri
                break
    ctypes = {}
    rdf_types = list(graph.objects(resource.uri, RDF.type)) + [None]
    for typ in rdf_types:
        for _, ctype, ext in iter_serializers(typ):
            if ext is not None  and  ctype not in ctypes:
                ctypes[ctype] = ext
    return serialize_htmlized_turtle(graph, resource, bindings or {}, ctypes,
                                     generate_body=generate_obsels,
                                     )
