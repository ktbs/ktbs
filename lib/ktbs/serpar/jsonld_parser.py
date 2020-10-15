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
"""
import logging

from ktbs.namespace import KTBS
from rdfrest.cores.factory import factory


LOG = logging.getLogger(__name__)

from json import loads

from pyld.jsonld import load_document as default_load_document, normalize
from rdflib import Graph

from rdfrest.parsers import register_parser
from rdfrest.exceptions import ParseError


def load_document(url, _options):
    """
    A specialized document loader that proxies the kTBS context.
    """
    if url == CONTEXT_URI:
        return {
            'contentType': 'application/ld+json',
            'contextUrl': None,
            'documentUrl': CONTEXT_URI,
            'document': CONTEXT_JSON,
        }
    else:
        return default_load_document(url)

def pylod_options(base_uri):
    return {
        'base': base_uri,
        'format': 'application/nquads',
        'documentLoader': load_document,
    }

@register_parser("application/ld+json", "jsonld", 85)
def parse_jsonld(content, base_uri=None, encoding="utf-8", graph=None):
    """I parse RDF content from JSON-LD.

    This parses the JSON as is.
    For handling "simplified" kTBS JSON, see parse_jdon
    (and use the application.json content-type).

    See :func:`rdfrest.parse.parse_rdf_xml` for prototype
    documentation.
    """
    if graph is None:
        graph = Graph()
    if encoding.lower() != "utf-8":
        content = content.decode(encoding).encode("utf-8")
    try:
        json_data = loads(content)
        # ... then parse!
        normalized_json = normalize(json_data, pylod_options(base_uri))
        # Do not use "nt" as format as it works only with latin-1
        graph.parse(data=normalized_json, format="n3")
    except Exception as ex:
        raise ParseError(ex.args[0] or str(ex))
    #print(graph.serialize(format="turtle", encoding='utf-8').decode('utf-8'))
    return graph

@register_parser("application/json", "json", 60)
def parse_json(content, base_uri=None, encoding="utf-8", graph=None):
    """I parse RDF content from kTBS-specific JSON.

    See :func:`rdfrest.parse.parse_rdf_xml` for prototype
    documentation.
    """
    if graph is None:
        graph = Graph()
    if encoding.lower() != "utf-8":
        content = content.decode(encoding).encode("utf-8")
    try:
        json_data = loads(content)
        obsel_context = False
        if isinstance(json_data, list):
            # this is a list of obsels ; embed it in correct
            json_data = {
                "@id": base_uri,
                "obsels": json_data,
            }
            obsel_context = True
        elif json_data.get("@type") == "Base":
            if 'inBase' not in json_data:
                json_data.setdefault('inRoot', str(base_uri))
                # NB: we should instead use 'inBase' when the target is a Base,
                # but we do not know the target at this point.
                # So ktbs.engine.base handles this special case,
                # and will replace it with the correct predicate.

        elif json_data.get("@type") in ("StoredTrace",
                                        "ComputedTrace",
                                        "DataGraph",
                                        "TraceModel",
                                        "Method"):
            json_data.setdefault("inBase", str(base_uri))

        elif "@graph" in json_data:
            # this is a TraceModel
            # @graph must be a non-empty list,
            # with the first item representing the trace model
            json_data["@graph"][0].setdefault("inBase", str(base_uri))
        elif ((json_data.get("hasObselList") is None)
              and
              (json_data.get("hasTraceStatistics") is None)
              and
              (json_data.get("hasBuiltinMethod") is None)):
            # must be an obsel
            obsel_context = True
            json_data.setdefault("hasTrace", str(base_uri))

        # add context if needed
        if "@context" not in json_data:
            if not obsel_context:
                json_data["@context"] = CONTEXT_URI
            else:
                model_uri = factory(base_uri, [KTBS.AbstractTrace]).model_uri
                if model_uri[-1] not in { "/", "#" }:
                    model_uri += "#"
                json_data["@context"] = [
                    CONTEXT_URI,
                    { "m": str(model_uri) },
                ]


        # ... then parse!
        normalized_json = normalize(json_data, pylod_options(base_uri))
        # Do not use "nt" as format as it works only with latin-1
        graph.parse(data=normalized_json, format="n3")

    except Exception as ex:
        raise ParseError(ex.args[0] or str(ex))
    return graph


CONTEXT_URI = "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context"

CONTEXT_SRC = """{"@context":{
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "k": "http://liris.cnrs.fr/silex/2009/ktbs#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",

    "AttributeType": "k:AttributeType",
    "Base": "k:Base",
    "BuiltinMethod": "k:BuiltinMethod",
    "ComputedTrace": "k:ComputedTrace",
    "DataGraph": "k:DataGraph",
    "KtbsRoot": "k:KtbsRoot",
    "Method": "k:Method",
    "Obsel": "k:Obsel",
    "ObselType": "k:ObselType",
    "RelationType": "k:RelationType",
    "StoredTrace": "k:StoredTrace",
    "StoredTraceObsels": "k:StoredTraceObsels",
    "TraceStatistics": "k:TraceStatistics",
    "TraceModel": "k:TraceModel",

    "contains": { "@id": "k:contains", "@type": "@id" },
    "hasAttributeObselType": { "@id": "k:hasAttributeDomain", "@type": "@id" },
    "hasAttributeDatatype": { "@id": "k:hasAttributeRange", "@type": "@id" },
    "hasBase": { "@id": "k:hasBase", "@type": "@id" },
    "begin": { "@id": "k:hasBegin", "@type": "xsd:integer" },
    "beginDT": { "@id": "k:hasBeginDT", "@type": "xsd:dateTime" },
    "hasBuiltinMethod": { "@id": "k:hasBuiltinMethod", "@type": "@vocab" },
    "hasContext": { "@id": "k:hasContext", "@type": "@id" },
    "version": "k:hasVersion",
    "defaultSubject": "k:hasDefaultSubject",
    "hasDefaultSubject": { "@id": "k:hasDefaultSubject", "@type": "@id" },
    "diagnosis": "k:hasDiagnosis",
    "end": { "@id": "k:hasEnd", "@type": "xsd:integer" },
    "endDT": { "@id": "k:hasEndDT", "@type": "xsd:dateTime" },
    "hasMethod": { "@id": "k:hasMethod", "@type": "@vocab" },
    "hasModel": { "@id": "k:hasModel", "@type": "@id" },
    "obselCount": { "@id": "k:hasObselCount", "@type": "xsd:integer" },
    "hasObselList": { "@id": "k:hasObselCollection", "@type": "@id" },
    "hasTraceStatistics": { "@id": "k:hasTraceStatistics", "@type": "@id" },
    "origin": { "@id": "k:hasOrigin" },
    "parameter": "k:hasParameter",
    "hasParentMethod": { "@id": "k:hasParentMethod", "@type": "@vocab" },
    "hasParentModel": { "@id": "k:hasParentModel", "@type": "@id" },
    "hasRelationOrigin": { "@id": "k:hasRelationDomain", "@type": "@id" },
    "hasRelationDestination": { "@id": "k:hasRelationRange", "@type": "@id" },
    "hasSource": { "@id": "k:hasSource", "@type": "@id" },
    "hasSourceObsel": { "@id": "k:hasSourceObsel", "@type": "@id" },
    "subject": "k:hasSubject",
    "hasSubject": { "@id": "k:hasSubject", "@type": "@id" },
    "suggestedColor": "k:hasSuggestedColor",
    "suggestedSymbol": "k:hasSuggestedSymbol",
    "hasSuperObselType": { "@id": "k:hasSuperObselType", "@type": "@id" },
    "hasSuperRelationType": { "@id": "k:hasSuperRelationType", "@type": "@id" },
    "hasTrace": { "@id": "k:hasTrace", "@type": "@id" },
    "traceBegin": { "@id": "k:hasTraceBegin", "@type": "xsd:integer" },
    "traceBeginDT": { "@id": "k:hasTraceBeginDT", "@type": "xsd:dateTime" },
    "traceEnd": { "@id": "k:hasTraceEnd", "@type": "xsd:integer" },
    "traceEndDT": { "@id": "k:hasTraceEndDT", "@type": "xsd:dateTime" },
    "hasUnit": { "@id": "k:hasUnit", "@type": "@vocab" },

    "external": "k:external",
    "filter": "k:filter",
    "fsa": "k:fsa",
    "fusion": "k:fusion",
    "hrules": "k:hrules",
    "isparql": "k:isparql",
    "parallel": "k:parallel",
    "pipe": "k:pipe",
    "sparql": "k:sparql",

    "sequence": "k:sequence",
    "second": "k:second",
    "millisecond": "k:millisecond",

    "inRoot": { "@reverse": "k:hasBase", "@type": "@id" },
    "inBase": { "@reverse": "k:contains", "@type": "@id" },
    "obsels": { "@reverse": "k:hasTrace", "@type": "@id" },
    "isMethodOf": { "@reverse": "k:hasMethod", "@type": "@id" },
    "isParentMethodOf": { "@reverse": "k:hasParentMethod", "@type": "@id" },
    "isSourceOf": { "@reverse": "k:hasSource", "@type": "@id" },

    "label": "skos:prefLabel",
    "additionalType": { "@id": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type","@type": "@id" }
}}"""

CONTEXT_JSON=loads(CONTEXT_SRC)

# TODO LATER split this plugin into a customizable generic version for rdfrest,
# and a specialization of it for kTBS
