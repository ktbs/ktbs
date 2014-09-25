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

OAUTH_CONFIG = None
IP_WHITELIST = None


class MyUnauthorizedError(UnauthorizedError):
    def __init__(self, auth_endpoint, client_id, root_uri, message="", challenge=None, **headers):
        self.redirect_uri = auth_endpoint + "?client_id=" + client_id
        self.root_uri = root_uri
        self.headers = headers
        self.headers['Link'] = '<{r_uri}>; rel=oauth_resource_server'.format(r_uri=self.redirect_uri)
        super(MyUnauthorizedError, self).__init__(message, "OAuth2",
                                                  content_type="text/html",
                                                  **headers)

    def get_body(self):
        return """<!DOCTYPE html>
        <html>
          <head>
            <title>401 Unauthorized</title>
            <meta charset="utf-8"/>
            <link rel="github_auth_endpoint" class="oauth_resource_server" href="{redirect_auth_uri}">
            <link rel="successful_login_redirect" href="{root_uri}">
          </head>
          <body><h1>401 Unauthorized</h1>
          <a href="{redirect_auth_uri}">Log in with Github</a>.
          </body>
        </html>
        """.format(redirect_auth_uri=self.redirect_uri, root_uri=self.root_uri)


def start_plugin(_config):
    global OAUTH_CONFIG
    global IP_WHITELIST
    OAUTH_CONFIG = {opt_key: opt_value for opt_key, opt_value in _config.items('oauth_login')}
    IP_WHITELIST = OAUTH_CONFIG['ip_whitelist'].split(' ')
    register_pre_processor(AUTHENTICATION, preproc_authentication)
    register_pre_processor(AUTHORIZATION, preproc_authorization)


def stop_plugin():
    unregister_pre_processor(preproc_authentication)
    unregister_pre_processor(preproc_authorization)


def preproc_authentication(service, request, resource):
    session = request.environ['beaker.session']

    try:  # Succeed if the user has already been authenticated
        user_role = session['remote_user_role']
        LOG.debug("User {0} is authenticated".format(request.remote_user))

    except KeyError:  # User is not authenticated
        # If in the process of authenticating with Github.
        # Else, preproc_authorization() is called afterward to invite the user to login
        authenticate(request)

    except Exception, e:
        LOG.debug("An error occurred during authentication:\n{error_msg}".format(error_msg=e))

    else:  # If we manage to get the user role, we continue
        if user_role == 'admin':
            request.remote_user = request.remote_addr
        elif user_role == 'user':
            request.remote_user = session['client_oauth_id']
        else:
            # TODO authn with same route as inside "except KeyError"
            LOG.debug("User role should be 'user' or 'admin', got {user_role} instead. Re-doing authentication."
                      .format(user_role=user_role))


def authenticate(request):
    session = request.environ['beaker.session']
    if request.remote_addr in IP_WHITELIST:
        auth = request.authorization
        if not auth:
            raise UnauthorizedError()
        elif auth[0] == 'Basic' and auth[1] == 'YWRtaW46YWRtaW4=':  # TODO take the variable from the conf and do the hash here
            session['remote_user_role'] = 'admin'
            request.remote_user = request.remote_addr
    elif request.GET.getall('code'):
        session['client_oauth_id'] = github_flow(request)
        session['remote_user_role'] = 'user'
        LOG.debug("User {0} has been successfully authenticated".format(session['client_oauth_id']))
        raise RedirectException('/')


def github_flow(request):
    # Exchange code for an access_token
    data = {
        'code': request.GET.getall('code')[0],
        'client_id': OAUTH_CONFIG['client_id'],
        'client_secret': OAUTH_CONFIG['client_secret']
    }
    enc_data = urllib.urlencode(data)
    gh_resp = urllib.urlopen(OAUTH_CONFIG['access_token_endpoint'], data=enc_data)
    gh_resp_qs = urlparse.parse_qs(gh_resp.read())
    access_token = gh_resp_qs[b'access_token'][0].decode('utf-8')
    # Exchange access_token for user id.
    gh_resp_id = urllib.urlopen('{api_url}?access_token={at}'
                                .format(api_url=OAUTH_CONFIG['api_endpoint'], at=access_token))
    gh_resp_id = gh_resp_id.read().decode('utf-8')
    resp_id_dec = json.loads(gh_resp_id)
    return str(resp_id_dec['id'])


def preproc_authorization(service, request, resource):
    session = request.environ['beaker.session']
    if request.remote_user is None:
        raise MyUnauthorizedError(OAUTH_CONFIG['auth_endpoint'], OAUTH_CONFIG['client_id'], service.root_uri)
    if "logout" in request.GET:
        user_id = session['client_oauth_id']
        session.delete()
        LOG.debug("User {0} has successfully logged out".format(user_id))
        raise UnauthorizedError("logged out", challenge="logged out")
