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
import logging
from rdfrest.http_server import \
    register_middleware, unregister_middleware, TOP
from webob import Request

LOG = logging.getLogger(__name__)

ALLOW_ORIGIN = None

class CorsMiddleware(object):
    #pylint: disable=R0903
    #  too few public methods

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)
        response = request.get_response(self.app)

        if ALLOW_ORIGIN:
            origin = request.headers.get("origin")
            if origin and (origin in ALLOW_ORIGIN
                           or "*" in ALLOW_ORIGIN):
                response.headerlist.extend([
                    ("access-control-allow-origin", origin),
                    ("access-control-allow-credentials", "true"),
                    ("access-control-expose-headers", "etag"),
                ])
                if request.method.lower() == "options":
                    response.headerlist.append(
                        ("access-control-allow-methods",
                         "GET, HEAD, PUT, POST, DELETE")
                    )
                    acrh = request.headers.get("access-control-request-headers")
                    if acrh:
                        response.headerlist.append(
                            ("access-control-allow-headers", acrh)
                        )
            
        return response(environ, start_response)

def start_plugin(config):
    #pylint: disable=W0603
    
    global ALLOW_ORIGIN
    
    deprecated_allow_origin = config.get('server', 'cors-allow-origin')
    if deprecated_allow_origin:
        LOG.warning("configuration server.cors-allow-origin is deprecated; "
                    "use cors.allow-origin instead")
        ALLOW_ORIGIN = deprecated_allow_origin.split(" ")
        
    allow_origin = config.get('cors', 'allow-origin')
    if allow_origin:
        ALLOW_ORIGIN = allow_origin.split(" ")

    register_middleware(TOP, CorsMiddleware)


def stop_plugin():
    unregister_middleware(CorsMiddleware)
