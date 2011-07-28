#!/usr/bin/env python
#    This file is part of KTBS <http://liris.cnrs.fr/silex/2009/ktbs>
#    Copyright (C) 2009 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> / SILEX
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
I demonstrate the rdfrest framework with an example server.
"""
from os.path import abspath, dirname, join
from sys import path, stderr

SOURCE_DIR = dirname(dirname(abspath(__file__)))
LIB_DIR = join(SOURCE_DIR, "lib")
path.insert(0, LIB_DIR)
UTEST_DIR = join(SOURCE_DIR, "utest")
path.insert(0, UTEST_DIR)

from warnings import filterwarnings
#filterwarnings("ignore", category=DeprecationWarning, module="rdflib")
filterwarnings("ignore", category=UserWarning, module="rdflib")

import rdflib
assert rdflib.__version__.startswith("3.")

from wsgiref.simple_server import make_server

from rdfrest.http_front import HttpFrontend
from rdfrest_example import MyService, ONS, RNS

HOST = "localhost"
PORT = 8001
ROOT_URI = "http://%s:%s/" % (HOST, PORT)

def main():
    "The main function of this test"
    service = MyService(ROOT_URI)
    http = HttpFrontend(service, cache_control=cache_control)
    http.serializers.bind_prefix("", RNS)
    http.serializers.bind_prefix("o", ONS)
    print >> stderr, "===", "Starting server on ", ROOT_URI
    make_server(HOST, PORT, http).serve_forever()
    #make_server(HOST, PORT, http).handle_request()

def cache_control(resource):
    if str(resource.uri) == ROOT_URI:
        return None
    else:
        return "max-age=5"

if __name__ == "__main__":
    main()
