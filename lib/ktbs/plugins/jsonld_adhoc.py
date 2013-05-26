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
I provide kTBS JSON-LD serializers.
"""
from itertools import chain
from json import dumps
from rdflib import BNode, Literal, RDF, RDFS, URIRef, XSD
from rdflib.plugins.sparql.processor import prepareQuery
from rdfrest.parsers import wrap_exceptions
from rdfrest.serializers import get_prefix_bindings, iter_serializers, \
    register_serializer, SerializeError
from rdfrest.utils import coerce_to_uri
from re import compile as Regex

from ..namespace import KTBS, KTBS_NS_URI

def encode_unicodes(func):
    """I decorate a generator of unicodes to make it a generator of UTF8 str"""
    def wrapped(*args, **kw):
        for i in func(*args, **kw):
            yield i.encode("utf-8")
    return wrapped

def default_compact(uri):
    """I compact a URI using KTBS_NS_URI as the default vocabulary"""
    uri = str(uri)
    if uri.startswith(KTBS_NS_URI):
        ret = uri[len(KTBS_NS_URI)+1:]
    else:
        ret = uri
    return ret
    
def val2json(val, compact=default_compact):    
    """I convert a value into a JSON value"""
    if isinstance(val, BNode):
        return u"{}" # TODO recurse?
    elif isinstance(val, URIRef):
        return u"""{ "@id": "%s" }""" % compact(val)
    elif isinstance(val, Literal):
       if val.datatype in (XSD.integer, XSD.double, XSD.decimal, XSD.bool):
            return unicode(val)
    return dumps(unicode(val), ensure_ascii=False)

def iter_other_arcs(graph, uri, indent="    ",
                    predfunc=lambda x: x, objfunc=val2json ):
    "Yield JSON properties for all predicates outside the ktbs namespace."
    for pred, obj in graph.query(OTHER_ARCS, initBindings={"subj": uri}):
        yield u""",\n%s"%s": %s""" % (indent, predfunc(pred), objfunc(obj))

OTHER_ARCS = prepareQuery("""
    SELECT ?pred ?obj
    {
        ?subj ?pred ?obj .
        FILTER( substr(str(?pred), 1, %s) != "%s#" && ?pred != <%s>)
    } ORDER BY ?pred ?obj """ % (len(KTBS_NS_URI)+1, KTBS_NS_URI, RDF.type))

JSONLD = "application/ld+json"


@register_serializer(JSONLD, "json", 85, KTBS.Base)
@register_serializer("application/json", None, 60, KTBS.Base)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_base(graph, base, bindings=None):

    yield u"""\n{\n
    "@context": "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
    "@id": "%s",
    "@type": "Base" """ % base.uri

    label = base.state.value(base.uri, RDFS.label)
    if label:
        yield u""",\n    "label": %s """% val2json(label)

    contained = list(chain(
        base.iter_traces(),
        base.iter_models(),
        base.iter_methods()
    ))

    if contained:
        yield """,
    "contains": ["""

        comma =""
        for i in contained:
            yield """%s
        {
            "@id": "./%s",
            "@type": "%s"
        } """ % (
                comma,
                i.uri[len(base.uri):],
                i.RDF_MAIN_TYPE[len(KTBS_NS_URI)+1:],
                )
            comma = ", "

        yield """
    ] """


    yield u"""\n}\n"""

@register_serializer(JSONLD, "json", 85, KTBS.TraceModel)
@register_serializer("application/json", None, 60, KTBS.TraceModel)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_model(graph, tmodel, bindings=None):

    yield u"""\n{\n
    "@context": "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
    "@id": [
        {
            "@id": "",
            "@type": "TraceModel" """
    
    if tmodel.label:
        yield u""",\n            "label": %s """% val2json(tmodel.label)

    if tmodel.unit is not None:
        yield u""",\n            "unit": "%s" """ % str(tmodel.unit)

    parents = list(tmodel.parents)
    if parents:
        parents = ",".join( u'"%s"' % coerce_to_uri(i) for i in parents )
        yield u""",\n            "hasParentModel": [%s] """ % parents

    for i in iter_other_arcs(graph, tmodel.uri, "            ",):
        yield i

    for otype in tmodel.obsel_types:
        yield u"""
        },
        {
            "@id": "%s" ,
            "@type": "ObselType" """ % str(otype.uri)

        if otype.label:
            yield u""",\n            "label": %s """% val2json(otype.label)

        stypes = list(otype.supertypes)
        if stypes:
            stypes = ",".join( u'"%s"' % coerce_to_uri(i) for i in stypes )
            yield u""",\n            "hasSuperObselType": [%s] """ % stypes

        for i in iter_other_arcs(graph, otype.uri, "            ",):
            yield i
        
    for atype in tmodel.attribute_types:
        yield u"""
        },
        {
            "@id": "%s" ,
            "@type": "AttributeType" """ % str(atype.uri)

        if atype.label:
            yield u""",\n            "label": %s """% val2json(atype.label)

        if atype.obsel_type:
            yield u""",\n            "hasAttributeObselType": "%s" """ \
                % coerce_to_uri(atype.obsel_type)

        if atype.data_type:
            yield u""",\n            "hasAttributeDatatype": "%s" """ \
                % atype.data_type

        for i in iter_other_arcs(graph, atype.uri, "            ",):
            yield i

    for rtype in tmodel.relation_types:
        yield u"""
        },
        {
            "@id": "%s" ,
            "@type": "RelationType" """ % str(rtype.uri)

        if rtype.label:
            yield u""",\n            "label": %s """% val2json(rtype.label)

        stypes = list(rtype.supertypes)
        if stypes:
            stypes = ",".join( u'"%s"' % coerce_to_uri(i) for i in stypes )
            yield u""",\n            "hasSuperRelationType": [%s] """ % stypes

        if rtype.origin:
            yield u""",\n            "hasRelationOrigin": "%s" """ \
                % coerce_to_uri(rtype.origin)

        if rtype.destination:
            yield u""",\n            "hasRelationDestination": "%s" """ \
                % coerce_to_uri(rtype.destination)

        for i in iter_other_arcs(graph, rtype.uri, "            ",):
            yield i


    yield u"""
        }
    ]\n}\n"""


@register_serializer(JSONLD, "json", 85, KTBS.ComputedTrace)
@register_serializer(JSONLD, "json", 85, KTBS.StoredTrace)
@register_serializer("application/json", None, 60, KTBS.ComputedTrace)
@register_serializer("application/json", None, 60, KTBS.StoredTrace)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_trace(graph, trace, bindings=None):
    
    yield u"""\n{
    "@context": "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
    "@id": "%s",
    "@type": "%s" """ % (
        trace.uri,
        trace.RDF_MAIN_TYPE[len(KTBS_NS_URI)+1:],
        )
    if trace.label:
        yield u""",\n    "label": %s """% val2json(trace.label)
    yield u""",
    "hasModel": "%s",
    "origin": "%s",
    "hasObselList": "%s/@obsels" """ % (
        trace.model_uri,
        trace.origin,
        trace.uri,
        )

    if hasattr(trace, "default_subject"):
        yield u""",\n    "hasDefaultSubject": %s """ % \
            val2json(trace.default_subject)
    if trace.source_traces:
        sources = u", ".join( u'"%s"' % coerce_to_uri(i)
                              for i in trace.source_traces )
        yield u""",\n    "hasSource": [%s]""" % sources
    if hasattr(trace, "method"):
        yield u""",\n    "method": "%s" """% coerce_to_uri(trace.label)
        pad = trace.parameters_as_dict
        if pad:
            params = u", ".join( "%s=%s" % i for i in pad.items() )
            yield u""",\n    "parameter": [%s] """ % val2json(params)
            
    for i in iter_other_arcs(graph, trace.uri):
        yield i


    yield u"""\n}\n"""


@register_serializer(JSONLD, "json", 85, KTBS.ComputedTraceObsels)
@register_serializer(JSONLD, "json", 85, KTBS.StoredTraceObsels)
@register_serializer("application/json", None, 60, KTBS.ComputedTraceObsels)
@register_serializer("application/json", None, 60, KTBS.StoredTraceObsels)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_trace_obsels(graph, tobsels, bindings=None):
    trace_uri = tobsels.trace.uri
    model_uri = tobsels.trace.model_uri
    if model_uri[-1] not in { "/", "#" }:
        model_uri += "#"

    def compact(uri):
        uri = str(uri)
        if uri.startswith(model_uri):
            ret = "m:%s" % uri[len(model_uri):]
        elif uri.startswith(trace_uri):
            ret = "./%s" % uri[len(trace_uri):]
        elif uri.startswith(KTBS_NS_URI):
            ret = uri[len(KTBS_NS_URI)+1:]
        else:
            ret = uri
        return ret
    
    def myval2json(node):
        return val2json(node, compact)

    yield u"""\n{\n
    "@context": [
        "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
        { "m": "%s" }
    ],
    "@id": ".",
    "hasObselList": "@obsels",
    "obsels": [""" % model_uri

    obsels = graph.query("""
        PREFIX : <%s#>
        SELECT ?obs ?otype ?subject ?begin ?end
        {
            ?obs a ?otype ; :hasSubject ?subject ; :hasBegin ?begin ;
                 :hasEnd ?end ;
            .
        } ORDER BY ?begin ?end
    """ % KTBS_NS_URI)

    comma = u""
    for obs, otype, subject, begin, end in obsels:
        yield comma + u"""
        {
            "@id": "%s",
            "@type": "%s",
            "subject": "%s",
            "begin": %s,
            "end": %s""" % (compact(obs), compact(otype), subject, begin, end)

        source_obsels = list(graph.objects(obs, KTBS.hasSourceObsel))
        if source_obsels:
            source_obsels = ", ".join( '"%s"' % compact(i)
                                       for i in source_obsels )
            yield u""",\n            "hasSourceObsel": [%s]""" % source_obsels

        for i in iter_other_arcs(graph, obs, "            ",
                                 compact, myval2json):
            yield i

        yield u"""
        }"""
        comma = u"," # after first obsel, prefix others with a comma

    yield """
    ]\n}\n"""


def start_plugin():
    pass
