# -*- coding: utf-8 -*-

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
I contain useful namespace objects, as well as the definition of the kTBS
vocabulary.

This module can be run as a program to generate the description:

* with no argument, it will output the original version (Turtle, with a
  reader-friendly layout);
* with an rdflib format as its argument, it will first convert it to that
  format, but the result might not be as reader-friendly.
"""

from StringIO import StringIO

from rdflib import Graph, RDF, URIRef
from rdflib.namespace import ClosedNamespace

from rdfrest.cores.local import LocalCore, Service


KTBS_NS_URI = "http://liris.cnrs.fr/silex/2009/ktbs"
KTBS_NS_URIREF = URIRef(KTBS_NS_URI)

KTBS_NS_TTL = """
@base <%s> .
@prefix : <#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

<>
    a owl:Ontology;
    rdfs:label "kTBS vocabulary v0.9"@en, "Vocabulaire kTBS v0.9"@fr;
    owl:versionInfo "0.9";
    # TODO SOON more metadata about vocabulary?
.

################################################################
#
# Trace Based System Metamodel
#
################################################################

:KtbsRoot
    a owl:Class ;
    rdfs:label "kTBS root"@en, "Racine d'un kTBS"@fr;
.

    :hasBase
        a owl:ObjectProperty, owl:InverseFunctionalProperty ;
        rdfs:label "contains base"@en, "contient la base"@fr;
        rdfs:domain :KtbsRoot ;
        rdfs:range :Base ;
    .

    :hasBuiltinMethod
        a owl:ObjectProperty ;
        rdfs:label "owns built-in method"@en,
                   "possède la méthode pré-définie"@fr;
        rdfs:domain :KtbsRoot ;
        rdfs:range :BuiltinMethod ;
    .

    :hasVersion
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has version"@en, "a pour numéro de version"@fr;
        rdfs:domain :KtbsRoot ;
    .


:Base
    a owl:Class ;
    rdfs:label "Trace base"@en, "Base de trace"@fr;
.

    :contains
        a owl:ObjectProperty, owl:InverseFunctionalProperty ;
        rdfs:label "contains"@en,
                   "contient"@fr;
        rdfs:domain :Base ;
        rdfs:range [ a owl:Class ;
                     owl:unionOf (:TraceModel :AbstractTrace :Method) ] ;
    .

:TraceModel
    a owl:Class ;
    rdfs:label "Trace model"@en, "Modèle de trace"@fr;
.

    :hasParentModel
        a owl:ObjectProperty ;
        rdfs:label "has parent model"@en, "a pour modèle parent"@fr;
        rdfs:domain :TraceModel ;
        rdfs:range :TraceModel ;
    .

    :hasUnit
        a owl:ObjectProperty, owl:FunctionalProperty ;
        rdfs:label "has unit"@en, "a pour unité"@fr;
        rdfs:domain :TraceModel ;
        rdfs:range :Unit ;
    .

:Unit
    a owl:Class ;
    rdfs:label "Temporal unit"@en, "Unité temporelle"@fr ;
.

:AbstractTrace
    a owl:Class ;
    rdfs:label "Any m-trace"@en, "M-trace quelconque"@fr;
.

    :hasModel
        a owl:ObjectProperty, owl:FunctionalProperty ;
        rdfs:label "has model"@en, "a pour modèle"@fr;
        rdfs:domain :AbstractTrace ;
        rdfs:range :TraceModel ;
    .

    :hasOrigin
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has origin"@en, "a pour origine"@fr;
        rdfs:domain :AbstractTrace ;
    .

    :hasDefaultSubject
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has default subject"@en, "a pour sujet par défaut"@fr;
        rdfs:domain :AbstractTrace ;
    .

    :hasSource
        a owl:ObjectProperty ;
        rdfs:label "has source m-trace"@en, "a pour m-trace source"@fr;
        rdfs:domain :AbstractTrace ;
        rdfs:range :AbstractTrace ;
    .

    :hasTraceBegin
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has begin"@en, "a pour début"@fr;
        rdfs:domain :AbstractTrace ;
        rdfs:range xsd:integer ;
    .

    :hasTraceEnd
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has end"@en, "a pour fin"@fr;
        rdfs:domain :AbstractTrace ;
        rdfs:range xsd:integer ;
    .

    :hasTraceBeginDT
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has begin date"@en, "a pour date de début"@fr;
        rdfs:domain :AbstractTrace ;
        rdfs:range xsd:dateTime ;
    .

    :hasTraceEndDT
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has end date"@en, "a pour date de fin"@fr;
        rdfs:domain :AbstractTrace ;
        rdfs:range xsd:dateTime ;
    .

:StoredTrace
    a owl:Class ;
    rdfs:subClassOf :AbstractTrace ;
    rdfs:label "Stored m-trace"@en, "M-trace stockée"@fr;
.

:ComputedTrace
    a owl:Class ;
    rdfs:subClassOf :AbstractTrace ;
    rdfs:label "Computed m-trace"@en, "M-trace calculée"@fr;
.

    :hasMethod
        a owl:ObjectProperty, owl:FunctionalProperty ;
        rdfs:label "has method"@en, "a pour méthode"@fr;
        rdfs:domain :ComputedTrace ;
        rdfs:range :AbstractMethod ;
    .

    :hasParameter
        a owl:DatatypeProperty ;
        rdfs:label "has parameter"@en, "a pour paramètre"@fr;
        rdfs:domain [ a owl:Class ;
                      owl:unionOf (:ComputedTrace :Method) ] ;
        rdfs:range xsd:string ;
    .

    :hasIntermediateSource
        a owl:ObjectProperty ;
        rdfs:label "has intermediate source m-trace"@en,
                   "a pour m-trace source intermédiaire"@fr;
        rdfs:domain :ComputedTrace ;
        rdfs:range :ComputedTrace ;
    .

:AbstractMethod
    a owl:Class ;
    rdfs:label "Any m-trace computation method"@en,
               "Une méthode quelconque de calcul de m-trace"@fr;
.

:BuiltinMethod
    a owl:Class ;
    rdfs:subClassOf :AbstractMethod ;
    rdfs:label "Built-in m-trace computation method"@en,
               "Méthode de calcul de m-trace pré-définie"@fr;
.    

:Method
    a owl:Class ;
    rdfs:subClassOf :AbstractMethod ;
    rdfs:label "User-defined m-trace computation method"@en,
               "Méthode de calcul de m-trace définie par l'utilisateur"@fr;
.    

    :hasParentMethod
        a owl:ObjectProperty, owl:FunctionalProperty ;
        rdfs:label "has parent method"@en, "a pour méthode parent"@fr;
        rdfs:domain :Method ;
        rdfs:range :AbstractMethod ;
    .

    #:hasParameter also has :Method in its domain (see above)

:Obsel
    a owl:Class ;
    rdfs:label "Obsel"@en, "Obsel"@fr ;
.

    :hasTrace
        a owl:ObjectProperty, owl:FunctionalProperty ;
        rdfs:label "belongs to m-trace"@en, "appartient à la m-trace"@fr;
        rdfs:domain :Obsel ;
        rdfs:range :AbstractTrace ;
    .

    :hasSubject
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has subject"@en, "a pour sujet"@fr;
        rdfs:domain :Obsel ;
    .

    :hasBegin
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has begin"@en, "a pour début"@fr;
        rdfs:domain :Obsel ;
        rdfs:range xsd:integer ;
    .

    :hasEnd
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has end"@en, "a pour fin"@fr;
        rdfs:domain :Obsel ;
        rdfs:range xsd:integer ;
    .

    :hasBeginDT
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has begin date"@en, "a pour date de début"@fr;
        rdfs:domain :Obsel ;
        rdfs:range xsd:dateTime ;
    .

    :hasEndDT
        a owl:DatatypeProperty, owl:FunctionalProperty ;
        rdfs:label "has end date"@en, "a pour date de fin"@fr;
        rdfs:domain :Obsel ;
        rdfs:range xsd:dateTime ;
    .

    :hasSourceObsel
        a owl:ObjectProperty ;
        rdfs:label "has source obsel"@en, "a pour obsel source"@fr;
        rdfs:domain :Obsel ;
        rdfs:range :Obsel ;
    .



# NB: as those classes are actually meta-classes
# they are defined using RDFS instead of OWL,
# so that trace model can safely be declared as OWL ontologies.

:ObselType
    a rdfs:Class ;
    rdfs:label "Obsel type"@en, "Type d'obsel"@fr ;
.

    :hasSuperObselType
        a rdf:Property ;
        rdfs:label "has super obsel type"@en, "a pour super-type d'obsel"@fr ;
        rdfs:domain :ObselType ;
        rdfs:range :ObselType ;
    .

:AttributeType
    a rdfs:Class ;
    rdfs:label "Attribute type"@en, "Type d'attriut"@fr ;
.

    :hasAttributeDomain
        a rdf:Property ;
        rdfs:label "applies to obsel type"@en, "s'applique au type d'obsel"@fr ;
        rdfs:domain :AttributeType ;
        rdfs:range :ObselType ;
    .

    :hasAttributeRange
        a rdf:Property ;
        rdfs:label "has datatype"@en, "a type de donnée"@fr ;
        rdfs:domain :AttributeType ;
        # TODO LATER should we use owl:Datatype? define our onw Datatype class?
    .


:RelationType
    a rdfs:Class ;
    rdfs:label "Relation type"@en, "Type de relation"@fr ;
.

    :hasSuperRelationType
        a rdf:Property ;
        rdfs:label "has super relation type"@en,
                   "a pour super-type de relation"@fr ;
        rdfs:domain :RelationType ;
        rdfs:range :RelationType ;
    .

    :hasRelationDomain
        a rdf:Property ;
        rdfs:label "has origin obsel type"@en,
                   "a pour type d'obsel d'origine"@fr ;
        rdfs:domain :RelationType ;
        rdfs:range :ObselType ;
    .

    :hasRelationRange
        a rdf:Property ;
        rdfs:label "has destination obsel type"@en,
                   "a pour type d'obsel de destination"@fr ;
        rdfs:domain :RelationType ;
        rdfs:range :ObselType ;
    .


################################################################
#
# Internal ontology
#
################################################################

#
# This ontology is not part of the M-Trace meta-model, but is used to describe
# the ancillary resources defined by kTBS to describe the elements of the
# meta-model (like obsel list of an m-trace).
#

    :hasPseudoMonRange
        a owl:DatatypeProperty, owl:FunctionalProperty;
        rdfs:label "has pseudo-monotonicity range"@en,
                   "a pour intervalle de pseudo-monotonicité"@fr;
        rdfs:domain :AbstractTrace ;
        rdfs:range xsd:integer ;
    .

    :hasObselCollection
        a owl:ObjectProperty, owl:FunctionalProperty,
          owl:InverseFunctionalProperty ;
        rdfs:label "has obsel list"@en, "a pour liste d'obsels"@fr;
        rdfs:domain :AbstractTrace ;
        rdfs:range :AbstractTraceObsels ;
    .

    :hasDiagnosis
        a owl:DatatypeProperty, owl:FunctionalProperty;
        rdfs:label "has diagnosis"@en, "a pour diagnostic"@fr;
        rdfs:domain :ComputedTrace ;
        rdfs:range xsd:string ;
    .

:AbstractTraceObsels
    a owl:Class ;
    rdfs:label "Obsel list of any m-trace"@en,
               "Liste d'obsels d'une m-trace quelconque"@fr;
.

:StoredTraceObsels
    a owl:Class ;
    rdfs:subClassOf :AbstractTraceObsels, 
        [   a owl:Restriction ;
            owl:onProperty [ owl:inverseOf :hasObselCollection ] ;
            owl:someValuesFrom :StoredTrace ;
        ] ;
    rdfs:label "Obsel list of a stored m-trace"@en,
               "Liste d'obsels d'une m-trace stockée"@fr;
.

:ComputedTraceObsels
    a owl:Class ;
    rdfs:subClassOf :AbstractTraceObsels, 
        [   a owl:Restriction ;
            owl:onProperty [ owl:inverseOf :hasObselCollection ] ;
            owl:someValuesFrom :ComputedTrace ;
        ] ;
    rdfs:label "Obsel list of a computed m-trace"@en,
               "Liste d'obsels d'une m-trace calculée"@fr;
.

:StoredTrace
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty :hasObselCollection ;
        owl:someValuesFrom :StoredTraceObsels ;
    ].

:ComputedTrace
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty :hasObselCollection ;
        owl:someValuesFrom :ComputedTraceObsels ;
    ].


################################################################
#
# Built-in symbols supported by this implementation
#
################################################################

:external a :BuiltinMethod ; rdfs:label "external"@en, "externe"@fr .
:filter   a :BuiltinMethod ; rdfs:label "filter"@en,   "filtre"@fr .
:fusion   a :BuiltinMethod ; rdfs:label "fusion"@en,   "fusion"@fr .
:sparql   a :BuiltinMethod ; rdfs:label "SPARQL"@en,   "SPARQL"@fr .

:sequence    a :Unit ; rdfs:label "sequence"@en,    "séquence"@fr .
:second      a :Unit ; rdfs:label "second"@en,      "seconde"@fr .
:millisecond a :Unit ; rdfs:label "millisecond"@en, "milliseconde"@fr .

# TODO SOON define owl:sameAs of units with dbpedia URIs

""" % KTBS_NS_URI

KTBS_NS_GRAPH = Graph("IOMemory", identifier=KTBS_NS_URIREF)
KTBS_NS_GRAPH.load(StringIO(KTBS_NS_TTL), KTBS_NS_URIREF, "n3")

KTBS_IDENTIFIERS = set()

for subject, _, _ in KTBS_NS_GRAPH.triples((None, RDF.type, None)):
    if subject.startswith(KTBS_NS_URI):
        splitted = subject.split("#", 1)
        if len(splitted) > 1:
            KTBS_IDENTIFIERS.add(splitted[1])

KTBS = ClosedNamespace(KTBS_NS_URI + "#", 
                       KTBS_IDENTIFIERS,
                       )

class _KtbsNsResource(LocalCore):
    """I am the only resource class of KTBS_NS_SERVICE.

    KTBS_NS_SERVICE provides a local copy of the kTBS namespace.
    """
    # too few public methods (1/2) #pylint: disable=R0903
    RDF_MAIN_TYPE = URIRef("http://www.w3.org/2002/07/owl#Ontology")

    @classmethod
    def init_service(cls, service):
        """I populate a service the kTBS namespace at its root.
        """
        cls.create(service, KTBS_NS_URIREF, KTBS_NS_GRAPH)

from rdfrest.util.config import get_service_configuration

service_config = get_service_configuration()

service_config.set('server', 'fixed-root-uri', KTBS_NS_URI)
#rdflib_plugin.get("IOMemory", Store)(""),

KTBS_NS_SERVICE = Service(classes=[_KtbsNsResource], service_config=service_config,
                          init_with=_KtbsNsResource.init_service)

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        print KTBS_NS_TTL
    else:
        KTBS_NS_GRAPH.serialize(sys.stdout, sys.argv[1])
