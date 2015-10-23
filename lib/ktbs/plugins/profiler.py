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
This kTBS plugin allows to run the profiler on a per-request basis.

To enable the profiler, simply add 'profiler' as a URL parameter.

Note that the profiler does not run the exact same code as the normal code:
it converts to a list the iterable returned by the WSGI application,
to ensure that all the code is actually ran in the profiler
(rather than differed by a generator).
"""

from cProfile import runctx as run_in_profiler
from datetime import datetime
from os.path import join
from webob import Request

from rdfrest.http_server import \
    register_middleware, unregister_middleware, MyResponse, TOP

class ProfilerMiddleware(object):

    DIRECTORY = "/tmp"

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        req = Request(environ)
        params = req.GET # URL parameters, regardless of the actual method
        do_profiling = params.pop('profiler', None)
        if do_profiling is None:
            resp = req.get_response(self.app)
            return resp(environ, start_response)
        else:
            filename = '%s--%s--%s.profiler.dat' % (
                datetime.now().strftime('%Y-%m-%d-%H:%M:%S'),
                req.method,
                req.url.replace('/', '_'),
            )
            my_globals = dict(globals())
            run_in_profiler("""
global RET
resp = req.get_response(self.app)
RET = list(resp(environ, start_response))
""",
                            my_globals, locals(),
                            join(self.DIRECTORY, filename))
            return my_globals['RET']

def start_plugin(config):
    register_middleware(TOP, ProfilerMiddleware)
    if config.has_section('profiler') and config.has_option('profiler', 'directory'):
        ProfilerMiddleware.DIRECTORY = config.get('profiler', 'directory')

def stop_plugin():
    unregister_middleware(ProfilerMiddleware)
