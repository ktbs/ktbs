# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011 Françoise Conil <francoise.conil@liris.cnrs.fr> /
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
I implement WSGI utility functions and classes.
"""

class SimpleRouter(object):
    """
    I implement a simple (even naive) route dispatcher.

    Not intended for production use -- merely for tests.
    """
    #pylint: disable-msg=R0903
    #    too few public methods

    def __init__(self, apps):
        """
        * app: an iterable of pairs (route, app)

        Routes are expected not include one-another.
        """
        self.routes = routes = []
        for route, app in apps:
            if not route.startswith('/'):
                route = "/%s" % route
            if route[-1] != '/':
                route = "%s/" % route
            routes.append((route, app))

    def __call__(self, env, start_response):
        for route, app in self.routes:
            if env["PATH_INFO"].startswith(route):
                env["PATH_INFO"] = env["PATH_INFO"][len(route)-1:]
                return app(env, start_response)
        start_response("404 Not Found", [])
        return []
