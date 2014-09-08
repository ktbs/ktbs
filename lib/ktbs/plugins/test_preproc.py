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
KTBS: Kernel for Trace-Based Systems.
"""

from rdfrest.http_server import \
     register_pre_processor, unregister_pre_processor, \
     RedirectException, UnauthorizedError, \
     AUTHENTICATION, AUTHORIZATION

class MyUnauthorizedError(UnauthorizedError):
    def __init__(self, message="", challenge=None, **headers):
        super(MyUnauthorizedError, self).__init__(message, "OAuth2",
                                                content_type="text/html",
                                                **headers)
    def get_body(self):
        return """<!DOCTYPE html>
        <html>
          <head><title>401 Unauthorized</title></head>
          <body><h1>401 Unauthorized</h1>
          <a href="">Login with [your favourite service]</a>
          </body>
        </html>
        """

def start_plugin():
    register_pre_processor(AUTHENTICATION, preproc1)
    register_pre_processor(AUTHORIZATION, preproc2)

def stop_plugin():
    unregister_pre_processor(preproc1)
    unregister_pre_processor(preproc2)


    
def preproc1(service, request, resource):
    auth = request.authorization
    print ("===", auth)
    if auth and auth[1] == "YWRtaW46YWRtaW4=":
        request.remote_user = "admin" # password: admin

def preproc2(service, request, resource):
    if request.remote_addr != "127.0.0.1":
        raise UnauthorizedError("wrong address")
    if request.remote_user is None:
        raise UnauthorizedError()
        #raise MyUnauthorizedError() # for OAuth2
    if "logout" in request.GET:
        raise UnauthorizedError("logged out", challenge="logged out")
