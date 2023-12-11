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
from collections import Counter, defaultdict, OrderedDict
from copy import deepcopy
from itertools import chain, groupby
from json import dumps
from rdflib import BNode, Literal, RDF, RDFS, URIRef, XSD
from rdflib.plugins.sparql.processor import prepareQuery
from pyld.jsonld import compact
from rdfrest.serializers import register_serializer, SerializeError
from rdfrest.util import coerce_to_uri, wrap_exceptions

from ..namespace import KTBS, KTBS_NS_URI
from ..utils import SKOS
from .jsonld_parser import CONTEXT_URI, load_document
from ..engine.trace_stats import NS as KTBS_NS_STATS

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
        if not prefixes:
            prefixes = {}
        prefixes.update({
            XSD: 'xsd',
            SKOS: 'skos',
            str(RDFS): 'rdfs',
        })
        self._prefixes = [
            (ns, prefix, len(str(ns))) for ns, prefix in prefixes.items()
        ]

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
                if not ret or ret[0] == '#':
                    ret = "./%s" % ret
                return ret or "./"
            elif self._parent and uri.startswith(self._parent):
                return "../%s" % uri[self._len_parent:]
        return uri

    @staticmethod
    def literal(val):
        if val.language:
            return { '@value': str(val), '@language': val.language }
        if val.datatype == XSD.integer:
            return int(val)
        elif val.datatype in (XSD.double, XSD.decimal):
            return float(val)
        elif val.datatype == XSD.boolean:
            return str(val) in ('true', '1')
        else:
            return str(val)

    def val2json(self, val, indent=""):
        return dumps(self.val2jsonobj(val), ensure_ascii=False, indent=4)

    def val2jsonobj(self, val, bnode_factory=lambda x: OrderedDict()):
        """I convert a value into a JSON basic type.
        val2json is a serialization of a JSON type !

        :param val: The value to be converted, val can be an RDF node or a
        list of RDF nodes
        """
        if isinstance(val, BNode):
            return bnode_factory(val)
        elif isinstance(val, URIRef):
            return OrderedDict({'@id': '%s' % self.uri(val)})
        elif isinstance(val, Literal):
            return self.literal(val)
        elif isinstance(val, list):
            return [ self.val2jsonobj(i) for i in val ]
        elif isinstance(val, dict) or isinstance(val, OrderedDict):
            # special case of obsel relations
            return val

        assert False, "unexpected value type %s" % type(val)

KTBS_SPECIAL_KEYS = {
    KTBS.hasBegin: "begin",
    KTBS.hasBeginDT: "beginDT",
    KTBS.hasEnd: "end",
    KTBS.hasEndDT: "endDT",
    KTBS.hasSubject: "subject",
}


def add_other_arcs(jsonobj, graph, uri, valconv, obsel=False):
    "Add to jsonobj properties for all predicates outside the ktbs namespace."

    valconv_uri = valconv.uri
    valconv_lit = valconv.literal
    pred_conv = valconv_uri

    if not obsel:
        types = [ i for i in graph.objects(uri, RDF.type)
                  if not i.startswith(KTBS_NS_URI) ]
        if types:
            types = [ valconv_uri(i) for i in types ]
            jsonobj['additionalType'] = types

    labels = [ valconv_lit(i) for i in graph.objects(uri, SKOS.prefLabel) ]
    if labels:
        jsonobj['label'] = labels[0]
        if len(labels) > 1:
            # for the sake of regularity, we keep a single value for "label",
            # and set the other values to the prefixed name
            jsonobj['skos:prefLabel'] = labels[1:]

    for pred, tuples in groupby(
            graph.query(OTHER_ARCS, initBindings={"subj": uri}),
            lambda tpl: tpl[1]
            ):
        if obsel:
            # include k:hasTrace property of related obsels
            obj = [ i[2]  if i[3] is None
                    else { "@id": valconv_uri(i[2]), "hasTrace": "./" }
                    for i in tuples ]
        else:
            obj = [ valconv.val2jsonobj(i[2]) for i in tuples ]
        if len(obj) == 1:
            obj = obj[0]
        jsonobj[pred_conv(pred)] = obj

    reverse = {}
    for pred, tuples in groupby(
            graph.query(OTHER_ARCS, initBindings={"obj": uri}),
            lambda tpl: tpl[1]
            ):
        if obsel:
            # include k:hasTrace property of related obsels
            subj = [ i[0]  if i[3] is None
                     else { "@id": valconv_uri(i[0]), "hasTrace": "./" }
                     for i in tuples ]
        else:
            subj = [ i[0] for i in tuples ]
        if len(subj) == 1:
            subj = subj[0]
        reverse[pred_conv(pred)] = subj
    if reverse:
        jsonobj['@reverse'] = reverse

def iter_other_arcs(graph, uri, valconv, indent="\n    ", obsel=False):
    "Yield JSON properties for all predicates outside the ktbs namespace."

    val2json = valconv.val2json
    valconv_uri = valconv.uri
    pred_conv = valconv_uri

    if not obsel:
        types = [ i for i in graph.objects(uri, RDF.type)
                  if not i.startswith(KTBS_NS_URI) ]
        if types:
            types = [ valconv_uri(i) for i in types ]
            yield """,%s "additionalType": %s""" % (indent, dumps(types))

    labels = list(graph.objects(uri, SKOS.prefLabel))
    if labels:
        yield """,%s"label": %s""" % (indent,
                                       val2json(labels[0], indent))
        if len(labels) > 1:
            # for the sake of regularity, we keep a single value for "label",
            # and set the other values to the full URI
            yield """,%s"%s": %s""" \
              % (indent, SKOS.prefLabel,
                 val2json(labels[1:], indent))

    for pred, tuples in groupby(
            graph.query(OTHER_ARCS, initBindings={"subj": uri}),
            lambda tpl: tpl[1]
            ):
        if obsel:
            # include k:hasTrace property of related obsels
            obj = [ i[2]  if i[3] is None
                    else { "@id": valconv_uri(i[2]), "hasTrace": "./" }
                    for i in tuples ]
        else:
            obj = [ i[2] for i in tuples ]
        if len(obj) == 1:
            obj = obj[0]
        yield """,%s"%s": %s""" % (indent, pred_conv(pred),
                                      val2json(obj, indent))

    comma = None
    for pred, tuples in groupby(
            graph.query(OTHER_ARCS, initBindings={"obj": uri}),
            lambda tpl: tpl[1]
            ):
        if comma is None:
            yield """,%s"@reverse": {""" % indent
            comma = ""
        if obsel:
            # include k:hasTrace property of related obsels
            subj = [ i[0]  if i[3] is None
                     else { "@id": valconv_uri(i[0]), "hasTrace": "./" }
                     for i in tuples ]
        else:
            subj = [ i[0] for i in tuples ]
        if len(subj) == 1:
            subj = subj[0]
        yield """%s%s    "%s": %s""" % (comma, indent, pred_conv(pred),
                                         val2json(subj, indent))
        comma = ","
    if comma is not None:
        yield "%s}" % indent

OTHER_ARCS = prepareQuery("""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX : <%s#>

    SELECT ?subj ?pred ?obj ?trc
    {
        ?subj ?pred ?obj .
        OPTIONAL { ?obj :hasTrace ?trc. ?subj :hasTrace ?trc. }
        FILTER( !regex(str(?pred), "^%s") &&
                ?pred NOT IN (rdf:type, skos:prefLabel) )
    } ORDER BY ?pred ?obj """
    % (KTBS_NS_URI, KTBS_NS_URI))



JSONLD = "application/ld+json"
JSON = "application/json"

@register_serializer(JSONLD, "jsonld", 85, KTBS.KtbsRoot)
@register_serializer(JSON, "json", 60, KTBS.KtbsRoot)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_root(graph, root, bindings=None):

    valconv = ValueConverter(root.uri)
    valconv_uri = valconv.uri
    valconv_lit = valconv.literal

    try:
        ktbs_version = next(graph.objects(root.uri, KTBS.hasVersion))
    except StopIteration:
        ktbs_version = "Unknwown"

    yield """{
    "@context": "%s",
    "@id": "%s",
    "@type": "KtbsRoot",
    "version": "%s",
    """ % (CONTEXT_URI, root.uri, ktbs_version)

    yield """
    "hasBuiltinMethod" : %s
    """ % dumps([ "%s" % valconv_uri(bm_uri)
                  for bm_uri in root.state.objects(root.uri,
                                                   KTBS.hasBuiltinMethod)])

    len_root_uri = len(root.uri)
    bases = []
    for b in root.iter_bases():
        bi = "%s" % b.uri[len_root_uri:]
        triples = graph.triples((b.uri, None, None))
        comments = []
        labels = []
        rdfs_labels = []
        for _, pred, obj in triples:
            if pred == RDFS.comment:
                comments.append(valconv_lit(obj))
            if pred == SKOS.prefLabel:
                labels.append(valconv_lit(obj))
            if pred == RDFS.label:
                rdfs_labels.append(valconv_lit(obj))
        if comments or labels or rdfs_labels:
            bi = { "@id": bi }
        if comments:
            if len(comments) == 1:
                comments = comments[0]
            bi['comment'] = comments
        if labels:
            bi['label'] = labels[0]
            if len(labels) > 1:
                bi['skosPrefLabel'] = labels[1:]
        if rdfs_labels:
            if len(rdfs_labels) == 1:
                rdfs_labels = rdfs_labels[0]
            bi['rdfs:label'] = rdfs_labels
        bases.append(bi)

    if len(bases):
        yield """,
    "hasBase" : %s
    """ % dumps(bases)

    for i in iter_other_arcs(graph, root.uri, valconv):
        yield i

    yield """\n}\n"""

@register_serializer(JSONLD, "jsonld", 85, KTBS.Base)
@register_serializer(JSON, "json", 60, KTBS.Base)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_base(graph, base, bindings=None):

    base_dict = OrderedDict()
    valconv = ValueConverter(base.uri)
    valconv_uri = valconv.uri
    valconv_lit = valconv.literal

    base_dict['@context'] = CONTEXT_URI
    base_dict['@id'] = base.uri
    base_dict['@type'] = 'Base'

    contained = chain(
        base.iter_traces(),
        base.iter_models(),
        base.iter_methods(),
        base.iter_bases(),
        base.iter_data_graphs(),
    )

    items = []
    len_base_uri = len(base.uri)
    for i in contained:
        item = OrderedDict()
        items.append(item)
        item['@id'] = i.uri[len_base_uri:]
        item['@type'] = i.RDF_MAIN_TYPE[LEN_KTBS:]

        # base enrichment
        rdfs_comments = [
            valconv_lit(j) for j in graph.objects(i.uri, RDFS.comment) ]
        if rdfs_comments:
            if len(rdfs_comments) > 1: rdfs_comments = rdfs_comments[0]
            item['rdfs:comment'] = rdfs_comments

        method = graph.value(i.uri, KTBS.hasMethod)
        if method:
            item['hasMethod'] = valconv_uri(method)

        model = graph.value(i.uri, KTBS.hasModel)
        if model:
            item['hasModel'] = valconv_uri(model)

        sources = [
            valconv_uri(j) for j in graph.objects(i.uri, KTBS.hasSource) ]
        if sources:
            item['hasSource'] = sources

        labels = [
            valconv_lit(j) for j in graph.objects(i.uri, SKOS.prefLabel) ]
        if labels:
            item['label'] = labels[0]
            if len(labels) > 1:
                item['skos:prefLabel'] = labels[1:]
        rdfs_labels = [
            valconv_lit(j) for j in graph.objects(i.uri, RDFS.label) ]
        if rdfs_labels:
            if len(rdfs_labels): rdfs_labels = rdfs_labels[0]
            item['rdfs:label'] = rdfs_labels

        obselCount = graph.value(i.uri, KTBS.hasObselCount)
        if obselCount is not None:
            item['obselCount'] = valconv_lit(obselCount)

    if items:
        base_dict['contains'] = items

    add_other_arcs(base_dict, graph, base.uri, valconv)

    if (None, KTBS.hasBase, base.uri) in graph:
        base_dict['inRoot'] = '../'
    else:
        base_dict['inBase'] = '../'

    yield dumps(base_dict, ensure_ascii=False, indent=4)


@register_serializer(JSONLD, "jsonld", 85, KTBS.Method)
@register_serializer(JSON, "json", 60, KTBS.Method)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_method(graph, method, bindings=None):

    valconv = ValueConverter(method.uri)
    valconv_uri = valconv.uri

    yield """{
    "@context": "%s",
    "@id": "%s",
    "@type": "Method",
    "hasParentMethod": "%s",
    "parameter": [""" % (
        CONTEXT_URI, method.uri, valconv_uri(coerce_to_uri(method.parent))
    )

    own_params = method.iter_parameters_with_values(False)
    yield ",".join(
        "\n        %s" % dumps("%s=%s" % item)
        for item in own_params
    ) + "]"

    used_by = list(method.state.subjects(KTBS.hasMethod, method.uri))
    if used_by:
        yield  """,\n        "isMethodOf": %s""" \
          % dumps([ valconv_uri(i) for i in used_by ])

    children = list(method.state.subjects(KTBS.hasParentMethod, method.uri))
    if children:
        yield  """,\n        "isParentMethodOf": %s""" \
          % dumps([ valconv_uri(i) for i in children])

    for i in iter_other_arcs(graph, method.uri, valconv):
        yield i

    yield """,\n    "inBase": "%s"\n}\n""" % valconv_uri(method.base.uri)


@register_serializer(JSONLD, "jsonld", 85, KTBS.TraceModel)
@register_serializer(JSON, "json", 60, KTBS.TraceModel)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_model(graph, tmodel, bindings=None):

    valconv = ValueConverter(tmodel.uri)
    valconv_uri = valconv.uri

    yield """{
    "@context": "%s",
    "@graph": [
        {
            "@id": "%s",
            "@type": "TraceModel",
            "inBase": "%s" """ \
    % (CONTEXT_URI, tmodel.uri, valconv_uri(tmodel.base.uri))

    if tmodel.unit is not None:
        yield """,\n            "hasUnit": "%s" """ \
          % valconv_uri(tmodel.unit)

    parents = list(tmodel.parents)
    if parents:
        parents = [ valconv_uri(coerce_to_uri(i)) for i in parents ]
        yield """,\n            "hasParentModel": %s""" % dumps(parents)

    for i in iter_other_arcs(graph, tmodel.uri, valconv, "\n            "):
        yield i

    for otype in tmodel.iter_obsel_types(False):
        yield """
        },
        {
            "@id": "%s" ,
            "@type": "ObselType" """ % valconv_uri(otype.uri)

        stypes = [ valconv_uri(coerce_to_uri(i))
                   for i in otype.iter_supertypes(False) ]
        if stypes:
            yield """,\n            "hasSuperObselType": %s """ \
              % dumps(stypes)

        suggested_color = otype.suggested_color
        if suggested_color:
            yield """,\n            "suggestedColor": %s """ \
              % dumps(suggested_color)

        suggested_symbol = otype.suggested_symbol
        if suggested_symbol:
            yield """,\n            "suggestedSymbol": %s """ \
              % dumps(suggested_symbol)

        for i in iter_other_arcs(graph, otype.uri, valconv, "\n            "):
            yield i

    for atype in tmodel.iter_attribute_types(False):
        yield """
        },
        {
            "@id": "%s" ,
            "@type": "AttributeType" """ % valconv_uri(atype.uri)

        obsel_types = atype.obsel_types
        if obsel_types:
            yield """,\n            "hasAttributeObselType": %s """ \
                % dumps([ valconv_uri(coerce_to_uri(ot)) for ot in obsel_types ])

        data_types = atype.data_types
        if data_types:
            yield """,\n            "hasAttributeDatatype": %s """ \
                % dumps([ valconv_uri(dt) for dt in data_types ])

        suggested_color = atype.suggested_color
        if suggested_color:
            yield """,\n            "suggestedColor": %s """ \
              % dumps(suggested_color)

        suggested_symbol = atype.suggested_symbol
        if suggested_symbol:
            yield """,\n            "suggestedSymbol": %s """ \
              % dumps(suggested_symbol)

        for i in iter_other_arcs(graph, atype.uri, valconv, "\n            "):
            yield i

    for rtype in tmodel.iter_relation_types(False):
        yield """
        },
        {
            "@id": "%s" ,
            "@type": "RelationType" """ % valconv_uri(rtype.uri)

        stypes = [ valconv_uri(coerce_to_uri(i))
                   for i in rtype.iter_supertypes(False) ]
        if stypes:
            yield """,\n            "hasSuperRelationType": %s """ \
              % dumps(stypes)

        origins = rtype.origins
        if origins:
            yield """,\n            "hasRelationOrigin": %s """ \
                % dumps([ valconv_uri(coerce_to_uri(o)) for o in origins ])

        destinations = rtype.destinations
        if destinations:
            yield """,\n            "hasRelationDestination": %s """ \
                % dumps([ valconv_uri(coerce_to_uri(d)) for d in destinations ],)

        suggested_color = rtype.suggested_color
        if suggested_color:
            yield """,\n            "suggestedColor": %s """ \
              % dumps(suggested_color)

        suggested_symbol = rtype.suggested_symbol
        if suggested_symbol:
            yield """,\n            "suggestedSymbol": %s """ \
              % dumps(suggested_symbol)

        for i in iter_other_arcs(graph, rtype.uri, valconv, "\n            "):
            yield i


    yield """
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

    yield """\n{
    "@context": "%s",
    "@id": "%s",
    "@type": "%s",
    "hasObselList": "./@obsels",
    "hasTraceStatistics": "./@stats" """ % (
        CONTEXT_URI,
        trace.uri,
        trace.RDF_MAIN_TYPE[LEN_KTBS:],
        )

    diagnosis = getattr(trace, 'diagnosis', None)
    if diagnosis is not None:  # can be None with faulty computed traces
        yield ',\n    "diagnosis": %s' % dumps(diagnosis)

    model_uri = trace.model_uri
    if model_uri is not None: # can be None with faulty computed traces
        yield ',\n    "hasModel": "%s"' % valconv_uri(model_uri)

    origin = trace.origin
    if origin is not None: # can be None with faulty computed traces
        yield ',\n    "origin": "%s"' % origin

    trace_begin = trace.get_trace_begin()
    if trace_begin is not None:
        yield ',\n    "traceBegin": %s' % trace_begin

    trace_begin_dt = graph.value(trace.uri, KTBS.hasTraceBeginDT)
    if trace_begin_dt is not None:
        yield ',\n    "traceBeginDT": %s' % val2json(trace_begin_dt)

    trace_end = trace.get_trace_end()
    if trace_end is not None:
        yield ',\n    "traceEnd": %s' % trace_end

    trace_end_dt = graph.value(trace.uri, KTBS.hasTraceEndDT)
    if trace_end_dt is not None:
        yield ',\n    "traceEndDT": %s' % val2json(trace_end_dt)
    defsubject = trace.state.value(trace.uri, KTBS.hasDefaultSubject)
    if defsubject:
        if isinstance(defsubject, URIRef):
            yield """,\n    "hasDefaultSubject": "%s" """ % \
                valconv_uri(defsubject)
        else:
            yield """,\n    "defaultSubject": %s """ % \
                val2json(defsubject)
    if trace.source_traces:
        sources = [ valconv_uri(coerce_to_uri(i))
                    for i in trace.source_traces ]
        yield """,\n    "hasSource": %s""" % dumps(sources)
    if hasattr(trace, "method"):
        yield """,\n    "hasMethod": "%s" """ \
          % valconv_uri(coerce_to_uri(trace.method))
        own_params = trace.list_parameters_with_values(False)
        if own_params:
            yield """,\n    "parameter": [%s\n    ]""" % (
                ",".join(
                    "\n        %s"
                    % dumps("%s=%s" % item)
                    for item in own_params
                )
            )

    if trace.context_uris:
        context_uris = [ valconv_uri(i) for i in trace.context_uris ]
        yield """,\n    "hasContext": %s""" % dumps(context_uris)

    transformed = [ valconv_uri(i)
                    for i in trace.state.subjects(KTBS.hasSource, trace.uri) ]
    if transformed:
        yield """,\n    "isSourceOf": %s""" % dumps(transformed)

    for i in iter_other_arcs(graph, trace.uri, valconv):
        yield i

    yield """,\n    "inBase": "../"\n}\n"""


def iter_obsel_arcs(graph, obs, valconv, indent=""):
    """
    I iter over the JSON-LD representation
    of optional properties of obsels in the ktbs namespace.
    """
    valconv_uri = valconv.uri
    val2json = valconv.val2json

    source_obsels = [ valconv_uri(i) for i in graph.objects(obs, KTBS.hasSourceObsel) ]
    if source_obsels:
            yield """,\n%s"hasSourceObsel": %s""" \
              % (indent, dumps(source_obsels))
    beginDT = graph.value(obs, KTBS.hasBeginDT)
    if beginDT:
            yield """,\n%s"beginDT": %s """ % (indent, val2json(beginDT))
    endDT = graph.value(obs, KTBS.hasEndDT)
    if endDT:
        yield """,\n%s"endDT": %s """ % (indent, val2json(endDT))


def trace_obsels_to_json(graph, tobsels, bindings=None):
    """
    I create an Ordered dictionary for a further json-ld serialization.

    :param graph: Obsel collection graph - OpportunisticObselCollection.get_state() ?
    :param tobsels: OpportunisticObselCollection(AbstractTraceObselsMixin) ktbs/api/trace.py
    :param bindings: ?
    :return: The dictionnary created.
    """
    tobsels_dict = OrderedDict()

    model_uri = tobsels.trace.model_uri
    if model_uri[-1] not in { "/", "#" }:
        model_uri += "#"
    valconv = ValueConverter(tobsels.uri, { model_uri: "m" })
    valconv_uri = valconv.uri
    val2jsonobj = valconv.val2jsonobj

    if (tobsels.uri, RDF.type, KTBS.StoredTraceObsels) in graph:
        tobsels_type = "StoredTraceObsels"
    else:
        tobsels_type = "ComputedTraceObsels"

    # Est-ce qu'on a une constante, un namespace pour le contexte ktbs jsonld ?
    tobsels_dict['@context'] = [
        CONTEXT_URI,
        {'m': model_uri}
    ]
    tobsels_dict['@id'] = './'
    tobsels_dict['hasObselList'] = {
        '@id': '',
        '@type': tobsels_type
    }
    tobsels_dict['obsels'] = obsel_list = []

    trace_uri = valconv_uri(tobsels.trace.uri)
    wbegin = set(graph.subjects(KTBS.hasBegin, None))
    wtrace = set(graph.subjects(KTBS.hasTrace, None))
    bnode_ref = Counter()
    node_by_id = defaultdict(dict)
    for i in wbegin:
        node_by_id[i] = d = deepcopy(_OBSEL_TEMPLATE)
        d['@id'] = valconv_uri(i)

    for subj, pred, obj in graph:
        node_dict = node_by_id[subj]

        # handle special predicates
        if pred == _RDF_TYPE:
            at_type = node_dict.get('@type')
            if at_type is None:
                node_dict['@type'] = valconv_uri(obj)
            else:
                if not type(at_type) is list:
                    node_dict['@type'] = at_type = [at_type]
                at_type.append(valconv_uri(obj))
            continue
        if pred == _KTBS_HAS_TRACE:
            # ignored here, implied by the 'obsels' key in the parent dict
            continue
        if pred == _KTBS_HAS_SOURCE_OBSEL:
            # '@id' is implied by hasSourceObsel
            node_dict['hasSourceObsel'].append(valconv_uri(obj))
            continue

        def bnode_factory(n):
            bnode_ref.update((n,))
            if bnode_ref[n] == 1:
                return node_by_id[n]
            else:
                bnode_id = '_:%s' % n
                node_by_id[n]['@id'] = bnode_id
                return {'@id': bnode_id}
            
        pred_key = KTBS_SPECIAL_KEYS.get(pred) or valconv_uri(pred)
        new_val = val2jsonobj(obj, bnode_factory)
        if obj in wtrace:
            new_val['hasTrace'] = trace_uri
        if pred_key == 'subject' and type(new_val) is OrderedDict:
            # nicer representation of URI subject
            pred_key = 'hasSubject'
            new_val = new_val['@id']

        old_val = node_dict.get(pred_key)
        if old_val is None:
            node_dict[pred_key] = new_val
        elif type(old_val) == list:
            old_val.append(new_val)
        else:
            node_dict[pred_key] = [old_val, new_val]

        if obj in wbegin:
            obj_dict = node_by_id[obj]
            rev_dict = obj_dict.get('@reverse')
            if rev_dict is None:
                rev_dict = obj_dict['@reverse'] = {}
            old_val = rev_dict.get(pred_key)
            new_val = { "@id": valconv_uri(subj) }
            if subj in wtrace:
                new_val["hasTrace"] = trace_uri
            if old_val is None:
                rev_dict[pred_key] = new_val
            elif type(old_val) == list:
                old_val.append(new_val)
            else:
                rev_dict[pred_key] = [old_val, new_val]

    for obs_id in wbegin:
        obs_dict = node_by_id[obs_id]
        todel = []
        for key, val in obs_dict.items():
            if val is None or val == []:
                todel.append(key)
        for key in todel:
            del obs_dict[key]
        obsel_list.append(obs_dict)

    obsel_list.sort(key=lambda x: (x['end'], x['begin'], x['@id']))

    return tobsels_dict

_OBSEL_TEMPLATE = OrderedDict([
    ('@id', None),
    ('@type', None),
    ('begin', None),
    ('beginDT', None),
    ('end', None),
    ('endDT', None),
    ('subject', None),
    ('hasSubject', None),
    ('hasSourceObsel', []),
])

_RDF_TYPE = RDF.type
_KTBS_HAS_TRACE = KTBS.hasTrace
_KTBS_HAS_SOURCE_OBSEL = KTBS.hasSourceObsel


@register_serializer(JSONLD, "jsonld", 85, KTBS.ComputedTraceObsels)
@register_serializer(JSONLD, "jsonld", 85, KTBS.StoredTraceObsels)
@register_serializer(JSON, "json", 60, KTBS.ComputedTraceObsels)
@register_serializer(JSON, "json", 60, KTBS.StoredTraceObsels)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_trace_obsels(graph, tobsels, bindings=None):
    """
    I serialize the trace obsels to a json-ld string.

    :param graph:
    :param tobsels:
    :param bindings:
    :return:
    """
    tobsels_dict = trace_obsels_to_json(graph, tobsels, bindings)

    yield dumps(tobsels_dict, ensure_ascii=False, indent=4)

def trace_stats_to_json(graph, tstats, bindings=None):
    """
    I create an Ordered dictionary for a further json-ld serialization.

    :param graph: ? graph
    :param tstats: TraceStatistics object
    :param bindings: ?
    :return: The dictionnary created.
    """
    tstats_dict = OrderedDict()

    trace_uri = tstats.trace.uri
    model_uri = tstats.trace.model_uri
    if model_uri[-1] not in { "/", "#" }:
        model_uri += "#"
    valconv = ValueConverter(trace_uri)
    valconv_uri = valconv.uri
    val2jsonobj = valconv.val2jsonobj

    tstats_dict['@context'] = CONTEXT_URI
    tstats_dict['@id'] = './'
    tstats_dict['hasTraceStatistics'] = {
        '@id': '',
        '@type': 'TraceStatistics'
    }

    initNs = {'': str(KTBS_NS_URI),
              'stats': str(KTBS_NS_STATS)
              }
    initBindings = {'trace': trace_uri}

    # How could I get predicates in the form stat:xxxxx
    # in the results, InitNs does not seem to be enough
    # Is it because of the filter clause ?
    stats_infos = graph.query("""
        SELECT ?pred ?obj
            $trace # selected solely to please Virtuoso
        {{
            $trace ?pred ?obj

            filter (strstarts(xsd:string(?pred), "{0:s}"))
        }}
    """.format(KTBS_NS_STATS),
                              initNs=initNs,
                              initBindings=initBindings)

    for pred, obj, _ in stats_infos:
        if pred != KTBS_NS_STATS.obselCountPerType:
            tstats_dict[pred] = val2jsonobj(obj)

    # Recover data inside blank nodes : another request needed
    stats_infos = graph.query("""
        SELECT ?bn ?pred ?obj
            $trace # selected solely to please Virtuoso
        {
            $trace stats:obselCountPerType ?bn .

            ?bn ?pred ?obj .
        }
        ORDER BY ?bn
        """,
                              initNs=initNs,
                              initBindings=initBindings)

    if len(stats_infos) > 0:
        tstats_dict[KTBS_NS_STATS.obselCountPerType] = ocpt =  []
        for bn, tuples in groupby(stats_infos, lambda tpl: tpl[0]):
            ot_infos = {}
            for _, pred, obj, _ in tuples:
                pred = str(pred) # cast URIRef to plain unicode
                ot_infos[pred] = val2jsonobj(obj)

            ocpt.append(ot_infos)

    compact_context = {'@context': [ CONTEXT_URI,
                                     {'stats': KTBS_NS_STATS,
                                    'stats:hasObselType': {'@type': '@id'},
                                    'm': model_uri}
                                   ]
                        }

    tstats_dict = compact(tstats_dict, compact_context,
                          {'base': tstats.uri,
                           'documentLoader': load_document})

    final = OrderedDict()
    final['@context'] = None
    final['@id'] = None
    final['hasTraceStatistics'] = None
    final['stats:obselCount'] = None
    # None as no meaning in jsonld, if there is no arc in the graph there
    # should be no value. We could remove the keys which values are None
    # instead of this test
    if tstats_dict.get('stats:minTime') is not None:
        final['stats:minTime'] = None
        final['stats:maxTime'] = None
        final['stats:duration'] = None
    final.update(tstats_dict)

    # PyLD return "@stats" for the current URI which is not wrong
    # but we prefer an empty string for the sake of consistency
    final['hasTraceStatistics']['@id'] = ''

    return final

@register_serializer(JSONLD, "jsonld", 85, KTBS.TraceStatistics)
@register_serializer(JSON, "json", 60, KTBS.TraceStatistics)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_trace_stats(graph, tstats, bindings=None):
    """
    I serialize the trace stats to a json-ld string.

    :param graph:
    :param tstats:
    :param bindings:
    :return:
    """
    tstats_dict = trace_stats_to_json(graph, tstats, bindings)

    yield dumps(tstats_dict, ensure_ascii=False, indent=4)

@register_serializer(JSONLD, "jsonld", 85, KTBS.Obsel)
@register_serializer(JSON, "json", 60, KTBS.Obsel)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_obsel(graph, obsel, bindings=None):
    trace_uri = obsel.trace.uri
    model_uri = obsel.trace.model_uri
    if model_uri[-1] not in { "/", "#" }:
        model_uri += "#"
    valconv = ValueConverter(obsel.uri, { model_uri: "m" })
    valconv_uri = valconv.uri
    val2json = valconv.val2json

    otypes = [ valconv_uri(i)
               for i in obsel.state.objects(obsel.uri, RDF.type) ]
    if len(otypes) == 1:
        otypes = otypes[0]

    yield """{
    "@context": [
        "%s",
        { "m": "%s" }
    ],
    "@id": "%s",
    "@type": %s, 
    "hasTrace": "%s",
    "begin": %s,
    "end": %s
    """ % (
        CONTEXT_URI,
        model_uri,
        obsel.uri,
        dumps(otypes),
        valconv_uri(trace_uri),
        obsel.get_begin(),
        obsel.get_end(),
        )

    subject = obsel.get_subject()
    if subject is not None:
        if isinstance(subject, URIRef):
            yield ',\n    "hasSubject": "%s"' % valconv_uri(subject)
        else:
            yield ',\n    "subject": "%s"' % subject

    for i in iter_obsel_arcs(graph, obsel.uri, valconv, "\n            "):
        yield i

    for i in iter_other_arcs(graph, obsel.uri, valconv, obsel=True):
        yield i

    yield """\n}\n"""

@register_serializer(JSONLD, "jsonld", 85, KTBS.DataGraph)
@register_serializer(JSON, "json", 60, KTBS.DataGraph)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_datagraph(graph, datagraph, bindings=None):
    valconv = ValueConverter(datagraph.uri)
    valconv_uri = valconv.uri
    val2jsonobj = valconv.val2jsonobj

    jsonobj = OrderedDict()
    jsonobj['@context'] = CONTEXT_URI
    statements = jsonobj['@graph'] = []

    triples = graph.query('SELECT ?s ?p ?o { ?s ?p ?o } ORDER BY ?s ?p')
    for subj, s_triples in groupby(triples, lambda t: t[0]):
        sjson = val2jsonobj(subj)
        statements.append(sjson)
        for pred, sp_triples in groupby(s_triples, lambda t: t[1]):
            pjson = sjson[valconv_uri(pred)] = [
                val2jsonobj(obj) for _, _, obj in sp_triples
            ]

    yield dumps(jsonobj, ensure_ascii=False, indent=4)
