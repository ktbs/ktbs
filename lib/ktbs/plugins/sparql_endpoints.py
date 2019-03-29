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
This kTBS plugin provides SPARQL endpoint [1] capabilities
to all the resources exposed by kTBS.

[1] http://www.w3.org/TR/sparql11-protocol/
"""

from rdfrest.http_server import \
    register_middleware, unregister_middleware, MyResponse, BOTTOM
from rdfrest.util.prefix_conjunctive_view import PrefixConjunctiveView
from warnings import warn
from webob import Request

class SparqlEndpointMiddleware(object):
    #pylint: disable=R0903
    #  too few public methods

    UPDATE = False

    POST_CTYPES = {
        "application/x-www-form-urlencoded",
        "application/sparql-query",
        "application/sparql-update",
    }

    ASK_CTYPES = {
        "application/sparql-results+xml": "xml",
        "application/sparql-results+json": "json",
    }

    SELECT_CTYPES = {
        "application/sparql-results+xml": "xml",
        "application/sparql-results+json": "json",
        "text/csv": "csv",
        #"text/tab-separated-values": "tsv", ## NOT IMPLEMENTED YET in rdflib
    }

    CONSTRUCT_CTYPES = [
        "text/turtle",
        "application/rdf+xml",
        "application/n-triples",
        "text/plain",
    ]


    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        req = Request(environ)
        if (req.method == "GET" and req.GET.getall("query")
        or req.method == "POST" and req.content_type in self.POST_CTYPES):
            resp = self.handle_sparql(req)
        else:
            # pass through request to the wrapped application
            resp = req.get_response(self.app)
        return resp(environ, start_response)

    def handle_sparql(self, request):
        """
        I handle a SPARQL request
        """
        resource = request.environ['rdfrest.resource']
        if request.method == "GET" \
        or request.content_type.startswith("application/sparql-"):
            param = request.GET
        else:
            param = request.POST
        scope = param.getall("scope") or ['graph']
        default_graph_uri = param.getall("default-graph-uri")
        named_graph_uri = param.getall("named-graph-uri")

        if not request.content_type.startswith("application/sparql-"):
            lst = param.getall("query")
            if len(lst) == 0:
                # NB: not rejecting several queries, because some services
                # provide the same query several times (YASGUI)
                return MyResponse("400 Bad Request\nQuery not provided",
                                  status="400 Bad Request",
                                  request=request)
            query = lst[0]
        else:
            query = request.body

        if len(scope) > 1:
            return MyResponse("400 Bad Request\nMultiple values for 'scope'.",
                              status="400 Bad Request",
                              request=request)
        scope = scope[0]

        # TODO LATER do something with default_graph_uri and named_graph_uri ?

        if request.content_type == "application/sparql-update":
            return self.do_update(request, resource, scope, query)
        else:
            return self.do_query(request, resource, scope, query)


    def do_query(self, request, resource, scope, query):
        if scope not in { 'graph', 'subtree' }:
            return MyResponse("400 Bad Request\nUnsupported scope '%s'." % scope,
                              status="400 Bad Request",
                              request=request)

        resource.force_state_refresh()
        if scope == 'subtree':
            graph = PrefixConjunctiveView(resource.uri, resource.service.store)
        else:
            # scope == 'graph'
            graph = resource.get_state()

        result = graph.query(query, base=resource.uri)

        if result.graph is not None:
            ctype = serfmt = (
                request.accept.best_match(self.CONSTRUCT_CTYPES)
                or "text/turtle"
            )
        elif result.askAnswer is not None:
            ctype = request.accept.best_match(self.ASK_CTYPES)
            if ctype is None:
                ctype = "application/sparql-results+json"
            serfmt = self.SELECT_CTYPES[ctype]
        else:
            ctype = request.accept.best_match(self.SELECT_CTYPES)
            if ctype is None:
                ctype = "application/sparql-results+json"
            serfmt = self.SELECT_CTYPES[ctype]
        try:
            return MyResponse(result.serialize(format=serfmt),
                              status="200 Ok",
                              content_type=ctype,
                              request=request)
        except Exception, ex:
            if ex.message.startswith(
                    "You performed a query operation requiring a dataset"):
                status = "403 Forbidden"
                return MyResponse("%s\n%s"
                                  % (status, ex.message),
                                  status=status,
                                  request=request)
            else:
                raise

    def do_update(self, request, resource, scope, query):
        if scope != 'graph':
            return MyResponse("400 Bad Request\nUnsupported scope '%s' for SPARQL update." % scope,
                              status="400 Bad Request",
                              request=request)

        try:
            with resource.edit() as editable_graph:
                query = "BASE <%s> %s" % (resource.uri, query)
                editable_graph.update(query)
        except Exception, ex:
                status = "400 Bad update query"
                return MyResponse("%s\n%s"
                                  % (status, ex.message),
                                  status=status,
                                  request=request)
        return MyResponse("200 Ok\nUpdate query executed",
                          status="200 Ok",
                          request=request)

def start_plugin(config):
    if config.has_section('sparql') and config.has_option('sparql', 'update_endpoints'):
        SparqlEndpointMiddleware.UPDATE = config.getboolean('sparql', 'update_endpoints')
    register_middleware(BOTTOM, SparqlEndpointMiddleware)

def stop_plugin():
    unregister_middleware(SparqlEndpointMiddleware)
