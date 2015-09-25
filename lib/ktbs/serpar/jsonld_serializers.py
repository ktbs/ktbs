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
from itertools import chain, groupby
from json import dumps
from rdflib import BNode, Literal, RDF, RDFS, URIRef, XSD
from rdflib.plugins.sparql.processor import prepareQuery
#from rdfrest.parsers import wrap_exceptions
from rdfrest.serializers import get_prefix_bindings, iter_serializers, \
    register_serializer, SerializeError
from rdfrest.util import coerce_to_uri, wrap_exceptions
from re import compile as Regex

from ..namespace import KTBS, KTBS_NS_URI
from ..utils import SKOS

LEN_KTBS = len(KTBS_NS_URI)+1

def encode_unicodes(func):
    """I decorate a generator of unicodes to make it a generator of UTF8 str"""
    def wrapped(*args, **kw):
        for i in func(*args, **kw):
            yield i.encode("utf-8")
    return wrapped

class ValueConverter(object):
    """
    I convert values to JSON-LD strings.
    """
    def __init__(self, base_uri=None, prefixes=None):
        self._base = base_uri
        if base_uri is not None:
            self._len_base = len(base_uri)
            self._base_hash = base_uri + "#"
            self._len_dir = len_dir = base_uri.rfind("/") + 1
            self._dir = base_uri[:len_dir]
            self._len_parent = len_par = base_uri.rfind("/", 0, len_dir-1) + 1
            self._parent = parent = base_uri[:len_par]
            if self._parent.endswith("//"):
                self._parent = None
        if prefixes:
            self._prefixes = [
                (ns, prefix, len(ns)) for ns, prefix in prefixes.items()
            ]
        else:
            self._prefixes = ()

    def uri(self, uri, _len_ktbs=LEN_KTBS):
        """Convert URI"""
        if uri.startswith(KTBS_NS_URI):
            return uri[_len_ktbs:]
        for ns, prefix, len_ns in self._prefixes:
            if uri.startswith(ns):
                return "%s:%s" % (prefix, uri[len_ns:])
        if self._base is not None:
            if uri.startswith(self._base_hash):
                return uri[self._len_base:]
            if uri.startswith(self._dir):
                ret = uri[self._len_dir:]
                return ret or "./"
            elif self._parent and uri.startswith(self._parent):
                return "../%s" % uri[self._len_parent:]
        return uri

    def val2json(self, val, indent=""):
        """I convert a value into a JSON value.

        val can be an RDF node or a list of RDF nodes
        """
        if isinstance(val, BNode):
            return u"{}" # TODO recurse?
        elif isinstance(val, URIRef):
            return u"""{ "@id": "%s" }""" % self.uri(val)
        elif isinstance(val, Literal):
           if val.datatype in (XSD.integer, XSD.double, XSD.decimal,
                               XSD.boolean):
               return unicode(val)
           # TODO other datatypes?
           else:
               return dumps(unicode(val), ensure_ascii=False)
        elif isinstance(val, list):
            return "[%s%s]" % (
                ", ".join(( "%s  %s" % (indent,
                                        self.val2json(i, indent+"    "))
                            for i in val )),
                indent
            )
        elif isinstance(val, dict):
            # special case of obsel relations
            return dumps(val)
        assert False, "unexpected value type %s" % type(val)


def iter_other_arcs(graph, uri, valconv, indent="\n    ", obsel=False):
    "Yield JSON properties for all predicates outside the ktbs namespace."

    val2json = valconv.val2json
    valconv_uri = valconv.uri
    if obsel:
        pred_conv = valconv_uri
    else:
        pred_conv = lambda x: x

    if not obsel:
        types = [ i for i in graph.objects(uri, RDF.type)
                  if not i.startswith(KTBS_NS_URI) ]
        if types:
            types = [ valconv_uri(i) for i in types ]
            yield u""",%s "additionalType": %s""" % (indent, dumps(types))

    labels = list(graph.objects(uri, SKOS.prefLabel))
    if labels:
        yield u""",%s"label": %s""" % (indent,
                                       val2json(labels[0], indent))
        if len(labels) > 1:
            # for the sake of regularity, we keep a single value for "label",
            # and set the other values to the full URI
            yield u""",%s"%s": %s""" \
              % (indent, SKOS.prefLabel,
                 val2json(labels[1:], indent))

    for pred, tuples in groupby(
            graph.query(OTHER_ARCS, initBindings={"subj": uri}),
            lambda tpl: tpl[1]
            ):
        if obsel:
            # include k:hasTrace property of related obsels
            obj = [ i[2]  if i[3] is None
                    else { u"@id": valconv_uri(i[2]), u"hasTrace": u"./" }
                    for i in tuples ]
        else:
            obj = [ i[2] for i in tuples ]
        if len(obj) == 1:
            obj = obj[0]
        yield u""",%s"%s": %s""" % (indent, pred_conv(pred),
                                      val2json(obj, indent))

    comma = None
    for pred, tuples in groupby(
            graph.query(OTHER_ARCS, initBindings={"obj": uri}),
            lambda tpl: tpl[1]
            ):
        if comma is None:
            yield u""",%s"@reverse": {""" % indent
            comma = ""
        if obsel:
            # include k:hasTrace property of related obsels
            subj = [ i[0]  if i[3] is None
                     else { u"@id": valconv_uri(i[0]), u"hasTrace": u"./" }
                     for i in tuples ]
        else:
            subj = [ i[0] for i in tuples ]
        if len(subj) == 1:
            subj = subj[0]
        yield u"""%s%s    "%s": %s""" % (comma, indent, pred_conv(pred),
                                         val2json(subj, indent))
        comma = ","
    if comma is not None:
        yield u"%s}" % indent

OTHER_ARCS = prepareQuery("""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX : <%s#>

    SELECT ?subj ?pred ?obj ?trc
    {
        ?subj ?pred ?obj .
        OPTIONAL { ?obj :hasTrace ?trc. ?subj :hasTrace ?trc. }
        FILTER( substr(str(?pred), 1, %s) != "%s#" &&
                ?pred NOT IN (rdf:type, skos:prefLabel) )
    } ORDER BY ?pred ?obj """
    % (KTBS_NS_URI, LEN_KTBS, KTBS_NS_URI))

JSONLD = "application/ld+json"
JSON = "application/json"


@register_serializer(JSONLD, "jsonld", 85, KTBS.KtbsRoot)
@register_serializer(JSON, "json", 60, KTBS.KtbsRoot)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_root(graph, root, bindings=None):

    valconv = ValueConverter(root.uri)
    valconv_uri = valconv.uri

    try:
        ktbs_version = graph.objects(root.uri, KTBS.hasVersion).next()
    except StopIteration:
        ktbs_version = "Unknwown"

    yield u"""{
    "@context": "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
    "@id": "%s",
    "@type": "KtbsRoot",
    "version": "%s",
    """ % (root.uri, ktbs_version)

    yield """
    "hasBuiltinMethod" : %s
    """ % dumps([ "%s" % valconv_uri(bm.uri)
                  for bm in root.iter_builtin_methods()])

    len_root_uri = len(root.uri)
    bases = [ "%s" % b.uri[len_root_uri:] for b in root.iter_bases()]
    if len(bases):
        yield """,
    "hasBase" : %s
    """ % dumps(bases)

    for i in iter_other_arcs(graph, root.uri, valconv):
        yield i

    yield u"""\n}\n"""

@register_serializer(JSONLD, "jsonld", 85, KTBS.Base)
@register_serializer(JSON, "json", 60, KTBS.Base)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_base(graph, base, bindings=None):

    valconv = ValueConverter(base.uri)

    yield u"""{
    "@context": "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
    "@id": "%s",
    "@type": "Base" """ % base.uri

    contained = list(chain(
        base.iter_traces(),
        base.iter_models(),
        base.iter_methods()
    ))

    if contained:
        yield """,
    "contains": ["""

        comma =""
        len_base_uri = len(base.uri)
        for i in contained:
            yield """%s
        {
            "@id": "./%s",
            "@type": "%s"
        } """ % (
                comma,
                i.uri[len_base_uri:],
                i.RDF_MAIN_TYPE[LEN_KTBS:],
                )
            comma = ", "

        yield """
    ]"""

    for i in iter_other_arcs(graph, base.uri, valconv):
        yield i

    yield u""",\n    "inRoot": ".."\n}\n"""


@register_serializer(JSONLD, "jsonld", 85, KTBS.Method)
@register_serializer(JSON, "json", 60, KTBS.Method)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_method(graph, method, bindings=None):

    valconv = ValueConverter(method.uri)
    valconv_uri = valconv.uri

    yield u"""{
    "@context": "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
    "@id": "%s",
    "@type": "Method",
    "hasParentMethod": "%s",
    "parameter": [""" % (
        method.uri, valconv_uri(coerce_to_uri(method.parent))
    )

    own_params = method.iter_parameters(False)
    yield u",".join(
        u"\n        %s" % dumps("%s=%s" % (key, method.get_parameter(key)))
        for key in own_params
    ) + "]"

    used_by = list(method.state.subjects(KTBS.hasMethod, method.uri))
    if used_by:
        yield  u""",\n        "isMethodOf": %s""" \
          % dumps([ valconv_uri(i) for i in used_by ])

    children = list(method.state.subjects(KTBS.hasParentMethod, method.uri))
    if children:
        yield  u""",\n        "isParentMethodOf": %s""" \
          % dumps([ valconv_uri(i) for i in children])

    for i in iter_other_arcs(graph, method.uri, valconv):
        yield i

    yield u""",\n    "inBase": "%s"\n}\n""" % valconv_uri(method.base.uri)


@register_serializer(JSONLD, "jsonld", 85, KTBS.TraceModel)
@register_serializer(JSON, "json", 60, KTBS.TraceModel)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_model(graph, tmodel, bindings=None):

    valconv = ValueConverter(tmodel.uri, { XSD: "xsd" })
    valconv_uri = valconv.uri

    yield u"""{
    "@context": "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
    "@graph": [
        {
            "@id": "%s",
            "@type": "TraceModel",
            "inBase": "%s" """ % (tmodel.uri, valconv_uri(tmodel.base.uri))

    if tmodel.unit is not None:
        yield u""",\n            "hasUnit": "%s" """ \
          % valconv_uri(tmodel.unit)

    parents = list(tmodel.parents)
    if parents:
        parents = [ valconv_uri(coerce_to_uri(i)) for i in parents ]
        yield u""",\n            "hasParentModel": %s""" % dumps(parents)

    for i in iter_other_arcs(graph, tmodel.uri, valconv, "\n            "):
        yield i

    for otype in tmodel.iter_obsel_types(False):
        yield u"""
        },
        {
            "@id": "%s" ,
            "@type": "ObselType" """ % valconv_uri(otype.uri)

        stypes = [ valconv_uri(coerce_to_uri(i))
                   for i in otype.iter_supertypes(False) ]
        if stypes:
            yield u""",\n            "hasSuperObselType": %s """ \
              % dumps(stypes)

        for i in iter_other_arcs(graph, otype.uri, valconv, "\n            "):
            yield i

    for atype in tmodel.iter_attribute_types(False):
        yield u"""
        },
        {
            "@id": "%s" ,
            "@type": "AttributeType" """ % valconv_uri(atype.uri)

        if atype.obsel_type:
            yield u""",\n            "hasAttributeObselType": "%s" """ \
                % valconv_uri(coerce_to_uri(atype.obsel_type))

        if atype.data_type:
            yield u""",\n            "hasAttributeDatatype": "%s" """ \
                % valconv_uri(atype.data_type)

        for i in iter_other_arcs(graph, atype.uri, valconv, "\n            "):
            yield i

    for rtype in tmodel.iter_relation_types(False):
        yield u"""
        },
        {
            "@id": "%s" ,
            "@type": "RelationType" """ % valconv_uri(rtype.uri)

        stypes = [ valconv_uri(coerce_to_uri(i))
                   for i in rtype.iter_supertypes(False) ]
        if stypes:
            yield u""",\n            "hasSuperRelationType": %s """ \
              % dumps(stypes)

        if rtype.origin:
            yield u""",\n            "hasRelationOrigin": "%s" """ \
                % valconv_uri(coerce_to_uri(rtype.origin),)

        if rtype.destination:
            yield u""",\n            "hasRelationDestination": "%s" """ \
                % valconv_uri(coerce_to_uri(rtype.destination),)

        for i in iter_other_arcs(graph, rtype.uri, valconv, "\n            "):
            yield i


    yield u"""
        } ]\n}\n"""


@register_serializer(JSONLD, "jsonld", 85, KTBS.ComputedTrace)
@register_serializer(JSONLD, "jsonld", 85, KTBS.StoredTrace)
@register_serializer(JSON, "json", 60, KTBS.ComputedTrace)
@register_serializer(JSON, "json", 60, KTBS.StoredTrace)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_trace(graph, trace, bindings=None):

    valconv = ValueConverter(trace.uri)
    val2json = valconv.val2json
    valconv_uri = valconv.uri

    yield u"""\n{
    "@context": "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
    "@id": "%s",
    "@type": "%s" """ % (
        trace.uri,
        trace.RDF_MAIN_TYPE[LEN_KTBS:],
        )

    yield u""",
    "hasModel": "%s",
    "origin": "%s",
    "hasObselList": "@obsels" """ % (
        valconv_uri(trace.model_uri),
        trace.origin,
        )

    defsubject = trace.state.value(trace.uri, KTBS.hasDefaultSubject)
    if defsubject:
        yield u""",\n    "defaultSubject": %s """ % \
            val2json(defsubject)
    if trace.source_traces:
        sources = [ valconv_uri(coerce_to_uri(i))
                    for i in trace.source_traces ]
        yield u""",\n    "hasSource": %s""" % dumps(sources)
    if hasattr(trace, "method"):
        yield u""",\n    "hasMethod": "%s" """ \
          % valconv_uri(coerce_to_uri(trace.method))
        own_params = trace.list_parameters(False)
        if own_params:
            yield u""",\n    "parameter": [%s\n    ]""" % (
                ",".join(
                    u"\n        %s"
                    % dumps("%s=%s" % (key, trace.get_parameter(key)))
                    for key in own_params
                )
            )

    transformed = [ valconv_uri(i)
                    for i in trace.state.subjects(KTBS.hasSource, trace.uri) ]
    if transformed:
        yield u""",\n    "isSourceOf": %s""" % dumps(transformed)

    for i in iter_other_arcs(graph, trace.uri, valconv):
        yield i

    yield u""",\n    "inBase": "../"\n}\n"""


def iter_obsel_arcs(graph, obs, valconv, indent=""):
    """
    I iter over the JSON-LD representation
    of optional properties of obsels in the ktbs namespace.
    """
    valconv_uri = valconv.uri
    val2json = valconv.val2json

    source_obsels = [ valconv_uri(i) for i in graph.objects(obs, KTBS.hasSourceObsel) ]
    if source_obsels:
            yield u""",\n%s"hasSourceObsel": %s""" \
              % (indent, dumps(source_obsels))
    beginDT = graph.value(obs, KTBS.hasBeginDT)
    if beginDT:
            yield u""",\n%s"beginDT": %s """ % (indent, val2json(beginDT))
    endDT = graph.value(obs, KTBS.hasEndDT)
    if endDT:
        yield u""",\n%s"endDT": %s """ % (indent, val2json(endDT))


@register_serializer(JSONLD, "jsonld", 85, KTBS.ComputedTraceObsels)
@register_serializer(JSONLD, "jsonld", 85, KTBS.StoredTraceObsels)
@register_serializer(JSON, "json", 60, KTBS.ComputedTraceObsels)
@register_serializer(JSON, "json", 60, KTBS.StoredTraceObsels)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_trace_obsels(graph, tobsels, bindings=None):

    trace_uri = tobsels.trace.uri
    model_uri = tobsels.trace.model_uri
    if model_uri[-1] not in { "/", "#" }:
        model_uri += "#"
    valconv = ValueConverter(trace_uri, { model_uri: "m" })
    valconv_uri = valconv.uri

    yield u"""{
    "@context": [
        "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
        { "m": "%s" }
    ],
    "@id": "./",
    "hasObselList": {"@id":"", "@type": "StoredTraceObsels" },
    "obsels": [""" % model_uri

    obsels = graph.query("""
        PREFIX : <%s#>
        SELECT ?obs ?otype ?subject ?begin ?end
        {
            ?obs a ?otype ; :hasSubject ?subject ; :hasBegin ?begin ;
                 :hasEnd ?end .
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
            "end": %s""" % (valconv_uri(obs), valconv_uri(otype),
                            subject, begin, end)

        for i in iter_obsel_arcs(graph, obs, valconv, "\n            "):
            yield i

        for i in iter_other_arcs(graph, obs, valconv, "\n            ", True):
            yield i

        yield u"""
        }"""
        comma = u"," # after first obsel, prefix others with a comma

    yield """
    ]\n}\n"""


@register_serializer(JSONLD, "jsonld", 85, KTBS.Obsel)
@register_serializer(JSON, "json", 60, KTBS.Obsel)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_obsel(graph, obsel, bindings=None):
    trace_uri = obsel.trace.uri
    model_uri = obsel.trace.model_uri
    if model_uri[-1] not in { "/", "#" }:
        model_uri += "#"
    valconv = ValueConverter(trace_uri, { model_uri: "m" })
    valconv_uri = valconv.uri
    val2json = valconv.val2json


    otypes = [ valconv_uri(i)
               for i in obsel.state.objects(obsel.uri, RDF.type) ]
    if len(otypes) == 1:
        otypes = otypes[0]

    yield u"""{
    "@context": [
        "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context",
        { "m": "%s" }
    ],
    "@id": "%s",
    "@type": %s, 
    "hasTrace": "%s",
    "begin": %s,
    "end": %s,
    "subject": "%s"
    """ % (
        model_uri,
        obsel.uri,
        dumps(otypes),
        valconv_uri(trace_uri),
        obsel.get_begin(),
        obsel.get_end(),
        obsel.get_subject(),
        )

    for i in iter_obsel_arcs(graph, obsel.uri, valconv, "\n            "):
        yield i

    for i in iter_other_arcs(graph, obsel.uri, valconv, obsel=True):
        yield i

    yield u"""\n}\n"""
