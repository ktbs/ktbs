#    This file is part of RDF-REST <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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

"""
I provide a JSON serializer.

This serializer is based on http://n2.talis.com/wiki/RDF_JSON_Specification
"""
from itertools import groupby
from rdflib import BNode, URIRef
from rdfrest.serializer import register

@register("application/json", "json", 10) 
def serialize_json(graph, _sregister, _base_uri=None):
    """
    I serialize model in the JSON format.
    """
    query = """
        SELECT ?s ?p ?o WHERE { ?s ?p ?o } ORDER BY ?s ?p ?o
    """
    results = graph.query(query)
    result_tree = (
        (subject, groupby(results_by_subject, lambda t: t[1]))
        for subject, results_by_subject in groupby(results, lambda t: t[0])
    )
    ret = "{\n"
    for subject, results_by_subject in result_tree:
        if isinstance(subject, URIRef):
            subject = "_:%s" % subject
        else:
            subject = str(subject)
        ret += "  %r : {\n" % subject

        for predicate, results_by_predicate in results_by_subject:
            ret += "    %r : [\n" % str(predicate)

            for triple in results_by_predicate:
                obj = triple[2]
                ret += "      {\n"
                if isinstance(obj, BNode):
                    obj = "_:%s" % obj
                    ret += '        "value": %r,\n' % obj
                    ret += '        "type": "bnode",\n'
                elif isinstance(obj, URIRef):
                    obj = str(obj)
                    ret += '        "value": %r,\n' % obj
                    ret += '        "type": "uri",\n'
                else: # literal
                    value = obj.encode("utf-8")
                    lang = obj.language
                    datatype = obj.datatype
                    ret += '        "value": %r,\n' % value
                    ret += '        "type": "literal",\n'
                    if lang:
                        ret += '        "lang": %r,\n' % lang
                    if datatype:
                        ret += '        "datatype": %r,\n' % str(datatype)
                ret += "      },\n"
            ret += "    ],\n"

        ret += "  },\n"
    ret += "}\n"
    yield ret
