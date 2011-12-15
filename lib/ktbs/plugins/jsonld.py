# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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

try:
    import pyld
except ImportError:
    pyld = None

if pyld:
    from json import loads
    from pyld.jsonld import triples
    from rdflib import BNode, Graph, Literal, URIRef

    from rdfrest.parser import register as register_parser
    from rdfrest.serializer import register as register_serializer
    from rdfrest.exceptions import ParseError

    from rdflib import RDF, RDFS
    from ktbs.namespaces import KTBS, KTBS_IDENTIFIERS

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
            # Subject analysis
            if s[:2] == "_:":
                s = BNode(s[2:])
            else:
                s = URIRef(s, base_uri)

            # Object analysis
            if isinstance(o, dict):
                if "@iri" in o:
                    o = o["@iri"]
                    if o[:2] == "_:":
                        o = BNode(o[2:])
                    else:
                        o = URIRef(o, base_uri)
                else:
                    assert "@literal" in o
                    o = Literal(
                            o["@literal"],
                            lang = o.get("@language"),
                            datatype = o.get("@datatype"),
                            )
            else:
                o = Literal(o)

            # Predicate analysis
            if "@type" in p:
                p = RDF.type
            else:
                p = URIRef(p, base_uri)

            # Il faudra :
            # - trouver le sujet à ajouter car ce n'est pas la Base mais KtbsRoot
            # - donc l'objet c'est le sujet : la base
            if o == KTBS.Base:
               #graph.add((URIRef(""), KTBS.hasBase, s))
               graph.add((URIRef(base_uri), KTBS.hasBase, s))

            graph.add((s, p, o))
            return (s, p, o)

        if context is not None:
            json = { u"@context": context, u"@subject": json }

        return list(triples(json, jld_callback))

    @register_parser("application/json")
    def parse_jsonld(content, base_uri=None, encoding="utf-8"):
        """I parse RDF content from JSON-LD.

        :param content:  a byte string
        :param base_uri: the base URI of `content`
        :param encoding: the character encoding of `content`

        :return: an RDF graph
        :rtype:  rdflib.Graph
        :raise: :class:`rdfrest.exceptions.ParseError`
        """
        graph = Graph()
        #TODO à coder :D
        #if isinstance(content, basestring):
        if encoding.lower() != "utf-8":
            content = content.decode(encoding).encode("utf-8")
        try:
            jsonData = loads(content)
            jsonld2graph(jsonData, base_uri, graph)
        except Exception, ex:
            raise ParseError(ex.message or str(ex), ex)
        return graph


    @register_serializer("application/json", "json") 
    def serialize_json(graph, sregister, base_uri=None):
        """I serialize an RDF graph as JSON-LD.

        :param graph:     an RDF graph
        :type  graph:     rdflib.Graph
        :param sregister: the serializer register this serializer comes from
                          (useful for getting namespace prefixes and other info)
        :type  sregister: SerializerRegister
        :param base_uri:  the base URI to be used to serialize

        :return: an iterable of UTF-8 encoded byte strings
        :raise: :class:`~rdfrest.exceptions.SerializeError` if the serializer can
                not serialize this given graph.

        .. important::

            Serializers that may raise a
            :class:`~rdfrest.exceptions.SerializeError` must *not* be implemented
            as generators, or the exception will be raised too late (i.e. when the
            `HttpFrontend` tries to send the response.
        """

        #TODO à coder :D


    CONTEXT = {}

    for i in KTBS_IDENTIFIERS:
        #TODO virer les préfixes "has" et la majuscule qui va derrière
        # ex "begin" qui correspond à ktbs:hasBegin
        CONTEXT[i] = unicode(KTBS[i])

    #TODO Ajouter un @coerce @iri pour certaines propriétés
    # pour toutes les propriétés qui prennent un URI comme valeur, il faut les mettre @coerce @iri

