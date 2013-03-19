# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
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
JSON-LD parser and serializer for KTBS.

The 2011 december version of this parser was based on :
https://github.com/digitalbazaar/pyld d45816708b1f8d7ec813a6d5b662b97ed9c2dda3
This 2012 february parser is based on :
https://github.com/digitalbazaar/pyld a0b45ed6a90874beec12e77dc20520f066e8bc37
"""
import logging

LOG = logging.getLogger(__name__)

try:
    import pyld
except ImportError:
    pyld = None # invalid name # pylint: disable=C0103

if pyld:
    from urlparse import unquote

    from json import loads, dumps
    from pyld.jsonld import triples, frame

    from rdflib import BNode, Graph, Literal, URIRef
    from rdflib import RDF

    from rdfrest.parsers import register_parser
    from rdfrest.serializers import register_serializer
    from rdfrest.exceptions import ParseError

    from ktbs.namespace import KTBS

    def jsonld2graph(json, base_uri, graph, context=None):
        """
        I feed an rdflib 'graph' with the JSON-LD interpretation of 'json'.

        If 'json' contains no or an incomplete context, an additional 
        'context' can be provided.

        :param json: the JSON-LD interpretation of 'json'
        :param graph: an rdflib Graph()
        :param context: additional context if needed
        """
        
        def jld_callback(s, p, o):
            """
            Insert extracted (s, p, o) to an rdflib graph.

            :param s: subject
            :param p: predicate
            :param o: object
            """
            #print "Entrant (s,p,o) : (", s, ",", p, ",", o, ")"

            # Subject analysis
            if s[:2] == "_:":
                s = BNode(s[2:])
            else:
                s = URIRef(s, base_uri)

            # Object analysis
            # The dictionary can be much more complex
            if isinstance(o, dict):
                if "@id" in o:
                    o = o["@id"]
                    if o[:2] == "_:":
                        o = BNode(o[2:])
                    else:
                        o = URIRef(o, base_uri)
                else:
                    assert "@value" in o
                    o = Literal(
                            o["@value"],
                            lang = o.get("@language"),
                            datatype = o.get("@type"),
                            )
            else:
                o = Literal(o)

            # Predicate analysis
            if "@type" in p:
                p = RDF.type
                # Ensure that object is really an URIRef, JSON-LD 3.3
                o = URIRef(o, base_uri)
            elif p.startswith("x-rev:"):
                p = URIRef(p[6:], base_uri)
                s, o = o, s
            else:
                p = URIRef(p, base_uri)

            #print "Sortant (s,p,o) : (", s, ",", p, ",", o, ")"
            graph.add((s, p, o))
            return (s, p, o)

        if context is not None:
            json = { u"@context": context, u"@id": json }

        return list(triples(json, jld_callback))

    def parse_jsonld(content, base_uri=None, encoding="utf-8", graph=None):
        """I parse RDF content from JSON-LD.

        See :func:`rdfrest.parse.parse_rdf_xml` for prototype
        documentation.
        """
        if graph is None:
            graph = Graph()
        #TODO à coder :D
        #if isinstance(content, basestring):
        if encoding.lower() != "utf-8":
            content = content.decode(encoding).encode("utf-8")
        try:
            json_data = loads(content)
            # expand KTBS context
            context = json_data["@context"]
            if isinstance(context, basestring):
                if context != CONTEXT_URI:
                    raise Exception("invalid context URI: %s" % context)
                json_data["@context"] = CONTEXT
            else:
                if not isinstance(context, list):
                    raise Exception("invalid context: %s" % context)
                try:
                    i = context.index(CONTEXT_URI)
                except ValueError:
                    raise Exception("invalid context, "
                                    "does not contains ktbs-jsonld-context")
                context[i] = CONTEXT
            # add implicit arc for POSTed data so that we don't loose
            # the json root once converted to an RDF graph
            if json_data["@type"] == "Base":
                json_data.setdefault("inRoot", "")
            elif json_data["@type"] in ("StoredTrace",
                                        "ComputedTrace",
                                        "TraceModel",
                                        "Method"): 
                json_data.setdefault("inBase", "")
            # ... then parse!
            jsonld2graph(json_data, base_uri, graph)
        except Exception, ex:
            raise ParseError(ex.message or str(ex), ex)
        #print graph.serialize(format="turtle")
        return graph

    def uri2iri(uri):
        """
        I convert an URI to an IRI.
        """
        return unquote(uri).decode("utf-8")

    def node2jld(node):
        """
        I convert an rdflib 'node' into the corresponding JSLON-LD object.
        """
        if isinstance(node, URIRef):
            return { u"@id": uri2iri(node) }
        elif isinstance(node, BNode):
            return { u"@id": u"_:%s" % node }
        else:
            assert isinstance(node, Literal)
            ret = { u"@value": unicode(node) }
            if node.language:
                ret[u"@language"] = unicode(node.language)
            if node.datatype:
                # TODO recognize and use built-in JSON datatypes
                ret[u"@type"] = uri2iri(node.datatype)
            if len(ret) == 1: # only @value
                ret = ret["@value"]
            return ret

    def serialize_json(graph, resource, _binding=None):
        """I serialize an RDF graph as JSON-LD.
           I serialize 'graph' in JSON-LD, using a frame if available.

        See :func:`rdfrest.serializer.serialize_rdf_xml` for prototype
        documentation.
        """
        is_obsels_graph = False

        local_graph = Graph()
        local_graph += graph

        json_obj = []
        base_uri = resource.uri

        for p in XREVS:
            rev_p = URIRef("x-rev:%s" % p)
            for s, o in local_graph.subject_objects(p):
                local_graph.remove((s, p, o))
                local_graph.add((o, rev_p, s))

        if (graph.value(predicate=RDF.type, 
                        object=KTBS.StoredTraceObsels) is not None) or \
           (graph.value(predicate=RDF.type, 
                        object=KTBS.ComputedTraceObsels) is not None):
            is_obsels_graph = True
            trace_uri = graph.value(object=base_uri, 
                                    predicate=KTBS.hasObselCollection)
            trace = resource.factory(trace_uri)
            trace_model = trace.get_model_uri()

        cache = {}
        for s, p, o in local_graph:
            sdict = cache.get(s)
            if sdict is None:
                sdict = cache[s] = node2jld(s)

            if p == RDF.type:
                p = u"@type"
                o = uri2iri(o)
            else:
                p = uri2iri(p)
                o = node2jld(o)

            oobj = sdict.get(p)
            if oobj is None:
                sdict[p] = o
            else:
                if not isinstance(oobj, list):
                    oobj = [oobj]
                    sdict[p] = oobj

                oobj.append(o)
            
        json_obj = list(cache.itervalues())

        object_types = cache.get(base_uri, {}).get("@type")
        if not isinstance(object_types, list):
            object_types = [object_types]

        context_dict = {}
        context_dict.update(CONTEXT)
        ktbs_frame = None
        for o in object_types:
            if o in KTBS_FRAME_TYPES:
                if is_obsels_graph:
                    if "m" not in context_dict:
                        context_dict["m"] = trace_model
                    ktbs_frame = {
                            u"@context": context_dict,
                            u"@type": KTBS_FRAME_TYPES[o],
                            u"obsels": []      # Only used for @obsels
                            }
                else:
                    ktbs_frame = {
                            u"@context": CONTEXT,
                            u"@type": KTBS_FRAME_TYPES[o],
                            }
                break

        if frame is not None:
            json_obj = frame(json_obj, ktbs_frame)
            if is_obsels_graph:
                context_list = json_obj["@context"] = []
                context_list.append(CONTEXT_URI)
                context_list.append({"m": trace_model})
                json_obj[u'obsels'].sort(key=lambda d: d[u'begin'])
            else:
                json_obj["@context"] = CONTEXT_URI

        if __debug__:
            return dumps(json_obj, indent=4)
        else:
            return dumps(json_obj)



    CONTEXT_URI = "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context"

    CONTEXT_JSON = """{
        "xsd": "http://www.w3.org/2001/XMLSchema#",

        "AttributeType": "http://liris.cnrs.fr/silex/2009/ktbs#AttributeType",
        "Base": "http://liris.cnrs.fr/silex/2009/ktbs#Base",
        "BuiltinMethod": "http://liris.cnrs.fr/silex/2009/ktbs#BuiltinMethod",
        "ComputedTrace": "http://liris.cnrs.fr/silex/2009/ktbs#ComputedTrace",
        "KtbsRoot": "http://liris.cnrs.fr/silex/2009/ktbs#KtbsRoot",
        "Method": "http://liris.cnrs.fr/silex/2009/ktbs#Method",
        "Obsel": "http://liris.cnrs.fr/silex/2009/ktbs#Obsel",
        "ObselType": "http://liris.cnrs.fr/silex/2009/ktbs#ObselType",
        "RelationType": "http://liris.cnrs.fr/silex/2009/ktbs#RelationType",
        "StoredTrace": "http://liris.cnrs.fr/silex/2009/ktbs#StoredTrace",
        "TraceModel": "http://liris.cnrs.fr/silex/2009/ktbs#TraceModel",

        "contains": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#contains", "@type": "@id" },
        "external": "http://liris.cnrs.fr/silex/2009/ktbs#external",
        "filter": "http://liris.cnrs.fr/silex/2009/ktbs#filter",
        "fusion": "http://liris.cnrs.fr/silex/2009/ktbs#fusion",
        "hasAttributeObselType": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasAttributeDomain", "@type": "@id" },
        "hasAttributeDatatype": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasAttributeRange", "@type": "@id" },
        "hasBase": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasBase", "@type": "@id" },
        "begin": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasBegin", "@type": "xsd:integer" },
        "beginDT": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasBeginDT", "@type": "xsd:dateTime" },
        "hasBuiltinMethod": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasBuiltinMethod", "@type": "@id" },
        "hasDefaultSubject": "http://liris.cnrs.fr/silex/2009/ktbs#hasDefaultSubject",
        "end": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasEnd", "@type": "xsd:integer" },
        "endDT": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasEndDT", "@type": "xsd:dateTime" },
        "hasMethod": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasMethod", "@type": "@id" },
        "hasModel": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasModel", "@type": "@id" },
        "hasObselList": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasObselCollection", "@type": "@id" },
        "origin": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasOrigin", "@type": "xsd:dateTime" },
        "parameter": "http://liris.cnrs.fr/silex/2009/ktbs#hasParameter",
        "hasParentMethod": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasParentMethod", "@type": "@id" },
        "hasParentModel": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasParentModel", "@type": "@id" },
        "hasRelationOrigin": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasRelationDomain", "@type": "@id" },
        "hasRelationDestination": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasRelationRange", "@type": "@id" },
        "hasSource": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasSource", "@type": "@id" },
        "hasSourceObsel": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasSourceObsel", "@type": "@id" },
        "subject": "http://liris.cnrs.fr/silex/2009/ktbs#hasSubject",
        "hasSuperObselType": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasSuperObselType", "@type": "@id" },
        "hasSuperRelationType": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasSuperRelationType", "@type": "@id" },
        "hasTrace": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasTrace", "@type": "@id" },
        "traceBegin": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasTraceBegin", "@type": "xsd:integer" },
        "traceBeginDT": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasTraceBeginDT", "@type": "xsd:dateTime" },
        "traceEnd": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasTraceEnd", "@type": "xsd:integer" },
        "traceEndDT": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasTraceEndDT", "@type": "xsd:dateTime" },
        "unit": "http://liris.cnrs.fr/silex/2009/ktbs#hasUnit",
        "sparql": "http://liris.cnrs.fr/silex/2009/ktbs#sparql",

        "inRoot": { "@id": "x-rev:http://liris.cnrs.fr/silex/2009/ktbs#hasBase", "@type": "@id" },
        "inBase": { "@id": "x-rev:http://liris.cnrs.fr/silex/2009/ktbs#contains", "@type": "@id" },
        "obsels": { "@id": "x-rev:http://liris.cnrs.fr/silex/2009/ktbs#hasTrace", "@type": "@id" },

        "label": "http://www.w3.org/2004/02/skos/core#prefLabel"
    }"""

    CONTEXT = loads(CONTEXT_JSON)

    XREVS = [ URIRef(jso["@id"][6:]) for jso in CONTEXT.values() 
            if isinstance(jso,dict) and jso["@id"][:6] == "x-rev:" ]

    KTBS_FRAME_TYPES = dict([ (uri2iri(x), uri2iri(x)) for x in 
                            (KTBS.KtbsRoot, KTBS.Base, KTBS.TraceModel, 
                             KTBS.StoredTrace, KTBS.ComputedTrace, 
                             KTBS.StoredTraceObsels, KTBS.ComputedTraceObsels,
                             KTBS.ObselType, KTBS.RelationType, 
                             KTBS.Obsel, KTBS.AttributeType, 
                             KTBS.BuiltinMethod)])

    KTBS_FRAME_TYPES[uri2iri(KTBS.StoredTraceObsels)] = \
                                                  uri2iri(KTBS.StoredTrace)
    KTBS_FRAME_TYPES[uri2iri(KTBS.ComputedTraceObsels)] =  \
                                                  uri2iri(KTBS.ComputedTrace)


def start_plugin():
    """Start the JSON-LD plugin for kTBS."""
    if pyld is None:
        LOG.error("Can not load plugin: pyld package is not available")
        return
    register_parser("application/json")(parse_jsonld)
    register_serializer("application/json", "json")(serialize_json)
    LOG.info("JSON-LD parser and serializer registered succesfully")

# TODO LATER split this plugin into a customizable generic version for rdfrest,
# and a specialization of it for kTBS
