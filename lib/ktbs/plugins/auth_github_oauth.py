# This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
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
    UnauthorizedError, RedirectException, \
    AUTHENTICATION, AUTHORIZATION

from logging import getLogger
LOG = getLogger(__name__)

# Necessary imports for OAuth2
import urllib, json, urlparse
from config_oauth import CLIENT_SECRET, CLIENT_ID

THIRD_PARTY_AUTH_ENDPOINT = 'https://github.com/login/oauth/authorize'
THIRD_PARTY_ACCESS_TOKEN_ENDPOINT = 'https://github.com/login/oauth/access_token'
THIRD_PARTY_API_ENDPOINT = 'https://api.github.com/user'


class MyUnauthorizedError(UnauthorizedError):
    def __init__(self, message="", challenge=None, **headers):
        self.redirect_uri = THIRD_PARTY_AUTH_ENDPOINT+"?client_id="+CLIENT_ID
        super(MyUnauthorizedError, self).__init__(message, "OAuth2",
                                                  content_type="text/html",
                                                  **headers)

    def get_body(self):
        return """<!DOCTYPE html>
        <html>
          <head profile="http://tools.ietf.org/html/rfc6749#section-1.1">
            <title>401 Unauthorized</title>
            <link id="github_auth_endpoint" rel="resource_server" href="{redirect_auth_uri}">
          </head>
          <body><h1>401 Unauthorized</h1>
          <a href="{redirect_auth_uri}">Log in with Github</a>.
          </body>
        </html>
        """.format(redirect_auth_uri=self.redirect_uri)


def start_plugin():
    register_pre_processor(AUTHENTICATION, preproc_authentication)
    register_pre_processor(AUTHORIZATION, preproc_authorization)


def stop_plugin():
    unregister_pre_processor(preproc_authentication)
    unregister_pre_processor(preproc_authorization)


def preproc_authentication(service, request, resource):
    session = request.environ['beaker.session']

    try:  # Succeed if user has been authenticated
        request.remote_user = session['client_oauth_id']
        LOG.debug("User {0} is authenticated".format(request.remote_user))

    except KeyError:  # User is not authenticated
        # If in the process of authenticating
        if request.GET.getall('code'):
            # Exchange code for an access_token
            data = {
                'code': request.GET.getall('code')[0],
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
            }
            enc_data = urllib.urlencode(data)
            gh_resp = urllib.urlopen(THIRD_PARTY_ACCESS_TOKEN_ENDPOINT, data=enc_data)
            gh_resp_qs = urlparse.parse_qs(gh_resp.read())
            access_token = gh_resp_qs[b'access_token'][0].decode('utf-8')
            # Exchange access_token for user id.
            gh_resp_id = urllib.urlopen('{api_url}?access_token={at}'
                                        .format(api_url=THIRD_PARTY_API_ENDPOINT, at=access_token))
            gh_resp_id = gh_resp_id.read().decode('utf-8')
            resp_id_dec = json.loads(gh_resp_id)
            user_id = resp_id_dec['id']
            # Set the user ID in the session
            session['client_oauth_id'] = str(user_id)
            LOG.debug("User {0} has been successfully authenticated".format(session['client_oauth_id']))
            raise RedirectException('/')

        # Else, preproc_authorization() is called afterward to invite the user to login


def preproc_authorization(service, request, resource):
    session = request.environ['beaker.session']
    if request.remote_addr != "127.0.0.1":
        raise UnauthorizedError("wrong address")
    if request.remote_user is None:
        raise MyUnauthorizedError()
    if "logout" in request.GET:
        user_id = session['client_oauth_id']
        session.delete()
        LOG.debug("User {0} has successfully logged out".format(user_id))
        raise UnauthorizedError("logged out", challenge="logged out")
