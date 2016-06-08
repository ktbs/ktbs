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
from collections import OrderedDict
from copy import deepcopy
from itertools import chain, groupby
from json import dumps
from rdflib import BNode, Literal, RDF, URIRef, XSD, Graph
from rdflib.plugins.sparql.processor import prepareQuery
from pyld.jsonld import compact
from rdfrest.serializers import register_serializer, SerializeError
from rdfrest.util import coerce_to_uri, wrap_exceptions

from ..namespace import KTBS, KTBS_NS_URI
from ..utils import SKOS
from .jsonld_parser import CONTEXT_URI, CONTEXT_JSON
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
        return dumps(self.val2jsonobj(val), ensure_ascii=False, indent=4)

    def val2jsonobj(self, val):
        """I convert a value into a JSON basic type.
        val2json is a serialization of a JSON type !

        :param val: The value to be converted, val can be an RDF node or a
        list of RDF nodes
        """
        if isinstance(val, BNode):
            return OrderedDict()
        elif isinstance(val, URIRef):
            return OrderedDict({'@id': '%s' % self.uri(val)})
        elif isinstance(val, Literal):
            if val.datatype == XSD.integer:
                return int(val)
            elif val.datatype in (XSD.double, XSD.decimal):
                return float(val)
            elif val.datatype == XSD.boolean:
                return unicode(val) in ('true', '1')
            else:
                return unicode(val)
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

    try:
        ktbs_version = graph.objects(root.uri, KTBS.hasVersion).next()
    except StopIteration:
        ktbs_version = "Unknwown"

    yield u"""{
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
    "@context": "%s",
    "@id": "%s",
    "@type": "Base" """ % (CONTEXT_URI, base.uri)

    contained = list(chain(
        base.iter_traces(),
        base.iter_models(),
        base.iter_methods(),
        base.iter_bases(),
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

    if (None, KTBS.hasBase, base.uri) in graph:
        yield u""",\n    "inRoot": ".."\n}\n"""
    else:
        yield u""",\n    "inBase": ".."\n}\n"""


@register_serializer(JSONLD, "jsonld", 85, KTBS.Method)
@register_serializer(JSON, "json", 60, KTBS.Method)
@wrap_exceptions(SerializeError)
@encode_unicodes
def serialize_json_method(graph, method, bindings=None):

    valconv = ValueConverter(method.uri)
    valconv_uri = valconv.uri

    yield u"""{
    "@context": "%s",
    "@id": "%s",
    "@type": "Method",
    "hasParentMethod": "%s",
    "parameter": [""" % (
        CONTEXT_URI, method.uri, valconv_uri(coerce_to_uri(method.parent))
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
    "@context": "%s",
    "@graph": [
        {
            "@id": "%s",
            "@type": "TraceModel",
            "inBase": "%s" """ \
    % (CONTEXT_URI, tmodel.uri, valconv_uri(tmodel.base.uri))

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

        obsel_types = atype.obsel_types
        if obsel_types:
            yield u""",\n            "hasAttributeObselType": %s """ \
                % dumps([ valconv_uri(coerce_to_uri(ot)) for ot in obsel_types ])

        data_types = atype.data_types
        if data_types:
            yield u""",\n            "hasAttributeDatatype": %s """ \
                % dumps([ valconv_uri(dt) for dt in data_types ])

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

        origins = rtype.origins
        if origins:
            yield u""",\n            "hasRelationOrigin": %s """ \
                % dumps([ valconv_uri(coerce_to_uri(o)) for o in origins ])

        destinations = rtype.destinations
        if destinations:
            yield u""",\n            "hasRelationDestination": %s """ \
                % dumps([ valconv_uri(coerce_to_uri(d)) for d in destinations ],)

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
    "@context": "%s",
    "@id": "%s",
    "@type": "%s",
    "hasObselList": "@obsels",
    "hasTraceStatistics": "@stats" """ % (
        CONTEXT_URI,
        trace.uri,
        trace.RDF_MAIN_TYPE[LEN_KTBS:],
        )

    diagnosis = getattr(trace, 'diagnosis', None)
    if diagnosis is not None:  # can be None with faulty computed traces
        yield u',\n    "diagnosis": %s' % dumps(diagnosis)

    model_uri = trace.model_uri
    if model_uri is not None: # can be None with faulty computed traces
        yield u',\n    "hasModel": "%s"' % valconv_uri(model_uri)

    model_uri = trace.model_uri
    if model_uri is not None: # can be None with faulty computed traces
        yield u',\n    "hasModel": "%s"' % valconv_uri(model_uri)

    origin = trace.origin
    if origin is not None: # can be None with faulty computed traces
        yield u',\n    "origin": "%s"' % origin

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


def trace_obsels_to_json(graph, tobsels, bindings=None):
    """
    I create an Ordered dictionary for a further json-ld serialization.

    :param graph: Obsel collection graph - OpportunisticObselCollection.get_state() ?
    :param tobsels: OpportunisticObselCollection(AbstractTraceObselsMixin) ktbs/api/trace.py
    :param bindings: ?
    :return: The dictionnary created.
    """
    tobsels_dict = OrderedDict()

    trace_uri = tobsels.trace.uri
    model_uri = tobsels.trace.model_uri
    if model_uri[-1] not in { "/", "#" }:
        model_uri += "#"
    valconv = ValueConverter(trace_uri, { model_uri: "m" })
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

    obsels = graph.query("""
        PREFIX : <%s#>
        SELECT ?obs ?pred ?other ?rev ?trc
        {
            ?obs :hasBegin ?begin ;
                 :hasEnd ?end .
            {
                ?obs ?pred ?other .
                BIND (0 as ?rev)
            }
            UNION
            {
                ?other ?pred ?obs .
                BIND (1 as ?rev)
            }
            OPTIONAL { ?other :hasTrace ?trc } .
        } ORDER BY ?end ?begin ?obs ?rev ?pred ?other
    """ % (KTBS_NS_URI))


    for obs, tuples in groupby(obsels, lambda tpl: tpl[0]):
        obs_dict = deepcopy(_OBSEL_TEMPLATE)
        obs_dict['@id'] = valconv_uri(obs)
        rev_dict = OrderedDict()

        for _, pred, other, rev, trc in tuples:

            # handle special predicates
            if pred == _RDF_TYPE and not rev:
                if obs_dict['@type'] is None:
                    obs_dict['@type'] = valconv_uri(other)
                else:
                    obs_dict['additionalType'].append(valconv_uri(other))
                continue
            if pred == _KTBS_HAS_TRACE:
                # ignored here, implied by the 'obsels' key in the parent dict
                continue
            if pred == _KTBS_HAS_SOURCE_OBSEL:
                # '@id' is implied by hasSourceObsel
                obs_dict['hasSourceObsel'].append(valconv_uri(other))
                continue


            if rev:
                the_dict = rev_dict
            else:
                the_dict = obs_dict

            pred_key = KTBS_SPECIAL_KEYS.get(pred) or valconv_uri(pred)
            new_val = val2jsonobj(other)
            if trc:
                # other has to be a URI, so new_val has to be a dict
                new_val['hasTrace'] = valconv_uri(trc)

            old_val = the_dict.get(pred_key)
            if old_val is None:
                the_dict[pred_key] = new_val
            elif type(old_val) == list:
                old_val.append(new_val)
            else:
                the_dict[pred_key] = [old_val, new_val]

        if rev_dict:
            obs_dict['@reverse'] = rev_dict

        todel = []
        for key, val in obs_dict.items():
            if val is None or val == []:
                todel.append(key)
        for key in todel:
            del obs_dict[key]

        obsel_list.append(obs_dict)

    return tobsels_dict

_OBSEL_TEMPLATE = OrderedDict([
    ('@id', None),
    ('@type', None),
    ('additionalType', None),
    ('begin', None),
    ('beginDT', None),
    ('end', None),
    ('endDT', None),
    ('subject', None),
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
    valconv = ValueConverter(trace_uri, { model_uri: "m" })
    valconv_uri = valconv.uri
    val2jsonobj = valconv.val2jsonobj

    tstats_dict['@id'] = './'
    tstats_dict['hasTraceStatistics'] = {
        '@id': '',
        '@type': 'TraceStatistics'
    }

    initNs = {'': unicode(KTBS_NS_URI),
              'stats': unicode(KTBS_NS_STATS)
              }
    initBindings = {'trace': trace_uri}

    # How could I get predicates in the form stat:xxxxx
    # in the results, InitNs does not seem to be enough
    # Is it because of the filter clause ?
    stats_infos = graph.query("""
        SELECT ?pred ?obj
        {{
            ?trace ?pred ?obj

            filter (strstarts(xsd:string(?pred), "{0:s}"))
        }}
    """.format(KTBS_NS_STATS),
                              initNs=initNs,
                              initBindings=initBindings)

    for pred, obj in stats_infos:
        if pred.find('obselCountPerType') == -1:
            if isinstance(obj, Literal):
                tstats_dict[pred] = obj.toPython()
            else:
                tstats_dict[pred] = obj

    # Recover data inside blank nodes : another request needed
    stats_infos = graph.query("""
        SELECT ?bn ?pred ?obj
        {
            ?trace stats:obselCountPerType ?bn .

            ?bn ?pred ?obj .
        }
        ORDER BY ?bn
        """,
                              initNs=initNs,
                              initBindings=initBindings)

    if len(stats_infos) > 0:
        tstats_dict[KTBS_NS_STATS.obselCountPerType] = []
        for bn, tuples in groupby(stats_infos, lambda tpl: tpl[0]):
            ot_infos = {}
            for _, pred, obj in tuples:
                if pred.find('hasObselType') != -1:
                    ot_infos[pred] = {'@id': obj,
                                      '@type': '@id'}
                elif isinstance(obj, Literal):
                        ot_infos[pred] = obj.toPython()
                else:
                    ot_infos[pred] = obj

            tstats_dict[KTBS_NS_STATS.obselCountPerType].append(ot_infos)

    compact_context = {'@context': {'m': model_uri,
                                    'stats': KTBS_NS_STATS}
                        }

    full_context = {'@context': [CONTEXT_URI,
                                 compact_context['@context']]
                    }

    tstats_dict = compact(tstats_dict, full_context)

    tstats_dict['@context'] = full_context['@context']

    return tstats_dict

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
    valconv = ValueConverter(trace_uri, { model_uri: "m" })
    valconv_uri = valconv.uri
    val2json = valconv.val2json


    otypes = [ valconv_uri(i)
               for i in obsel.state.objects(obsel.uri, RDF.type) ]
    if len(otypes) == 1:
        otypes = otypes[0]

    yield u"""{
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
        yield ',\n    "subject": "%s"' % subject

    for i in iter_obsel_arcs(graph, obsel.uri, valconv, "\n            "):
        yield i

    for i in iter_other_arcs(graph, obsel.uri, valconv, obsel=True):
        yield i

    yield u"""\n}\n"""
