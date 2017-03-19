# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2014 Françoise Conil <francoise.conil@liris.cnrs.fr> /
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
I provide a convenient way to build a helper service wrapping a single graph.
"""
from ConfigParser import SafeConfigParser
from rdflib import Graph, RDF, URIRef

from rdfrest.cores.local import LocalCore, Service


def make_helper_service(uri, graph, format=None):

    if isinstance(graph, basestring):
        assert format != None
        data = graph
        graph = Graph()
        graph.parse(data=data, format=format)
    else:
        assert isinstance(graph, Graph)

    config = SafeConfigParser(allow_no_value=True)
    config.add_section('rdf_database')
    config.set('rdf_database', 'repository', '')
    config.set('rdf_database', 'force-init', 'true')
    config.add_section('server')
    config.set('server', 'fixed-root-uri', uri)

    uri = URIRef(uri)

    rdf_type = graph.value(uri, RDF.type)
    assert isinstance(rdf_type, URIRef)

    class _HelperResource(LocalCore):
        """I am the only resource class of the helper service.
        """
        # too few public methods (1/2) #pylint: disable=R0903
        RDF_MAIN_TYPE = rdf_type

        @classmethod
        def init_service(cls, service):
            """I populate a helper service the corresponding graph.
            """
            cls.create(service, uri, graph)

    return Service(classes=[_HelperResource], service_config=config,
                          init_with=_HelperResource.init_service)
