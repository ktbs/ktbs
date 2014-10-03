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
    UnauthorizedError, RedirectException, HttpException, \
    AUTHENTICATION, AUTHORIZATION
from base64 import standard_b64encode
from logging import getLogger

# Necessary imports for OAuth2
import urllib
import json
import urlparse

LOG = getLogger(__name__)
OAUTH_CONFIG = None  # Dictionary for the OAuth2 configuration
IP_WHITELIST = []  # Set if it exists in the configuration
ADMIN_CREDENTIALS_HASH = None  # Base64 hash of "login:password" if admin credentials are set in the configuration


class OAuth2Unauthorized(UnauthorizedError):

    """Prompt a user to login using Github OAuth2."""

    def __init__(self, auth_endpoint, client_id, redirect_uri, message="", **headers):
        """Set the information about the Github OAuth2 endpoint and redirect URI.

        We provide the OAuth2 endpoint information to the user using:
        - "Link" in the HTTP header
        - Visual information in the HTML

        :param auth_endpoint: the Github OAuth2 authentication endpoint
        :param client_id: the client ID registered at Github for this application
        :param redirect_uri: the URI to send the user back to after he log in
        """
        self.oauth_endpoint_uri = auth_endpoint + "?client_id=" + client_id
        self.redirect_uri = redirect_uri
        self.headers = headers
        self.headers['Link'] = ['<{r_uri}>; rel=oauth_resource_server'
                                .format(r_uri=self.oauth_endpoint_uri),
                                '<{redirect_uri}>; rel=successful_login_redirect'
                                .format(redirect_uri=self.redirect_uri)]
        self.headers['Content-Type'] = "text/html"
        super(OAuth2Unauthorized, self).__init__(message, challenge="OAuth2", **self.headers)

    def get_body(self):
        """Display a minimalistic HTML page to prompt the user to login."""
        return """<!DOCTYPE html>
        <html>
          <head>
            <title>401 Unauthorized</title>
            <meta charset="utf-8"/>
          </head>
          <body><h1>401 Unauthorized</h1>
          <a href="{redirect_auth_uri}">Log in with Github</a>.
          </body>
        </html>
        """.format(redirect_auth_uri=self.oauth_endpoint_uri)


class AccessForbidden(HttpException):
    def __init__(self, redirect_uri, **headers):
        self.redirect_uri = redirect_uri
        self.headers = headers
        self.headers['Content-Type'] = "text/html"
        super(AccessForbidden, self).__init__(message="",
                                              status="403 Forbidden",
                                              **self.headers)

    def get_body(self):
        return """<!DOCTYPE html>
        <html>
          <head>
            <title>403 Forbidden</title>
            <meta charset="utf-8"/>
          </head>
          <body><h1>403 Forbidden</h1>
          <script>setTimeout(function() {{ window.location = "{redirect_uri}"; }}, 10000);</script>
          <p><a href="{redirect_uri}">Please go to your base</a>.</p>
          <p>You will be redirected in 10 s.</p>
          </body>
        </html>
        """.format(redirect_uri=self.redirect_uri)


def start_plugin(_config):
    """I get the configuration values from the main kTBS configuration.

    .. note:: This function is called automatically by the kTBS.
              It is called once when the kTBS starts, not at each request.
    """

    def section_dict(section_name):
        """Convert a configuration section to a Python dictionary"""
        if _config.has_section(section_name):
            return {opt_key: opt_value for opt_key, opt_value in _config.items(section_name)}
        else:
            return None

    global OAUTH_CONFIG
    global IP_WHITELIST
    global ADMIN_CREDENTIALS_HASH

    OAUTH_CONFIG = section_dict('oauth_login')

    admin_login_config = section_dict('admin_login')
    if admin_login_config:
        IP_WHITELIST = admin_login_config['ip_whitelist'].split(' ')
        ADMIN_CREDENTIALS_HASH = standard_b64encode(admin_login_config['login'] + ':' +
                                                    admin_login_config['password'])

    # We register two functions to call (in order) at each request
    register_pre_processor(AUTHENTICATION, preproc_authentication)
    register_pre_processor(AUTHORIZATION, preproc_authorization)


def stop_plugin():
    unregister_pre_processor(preproc_authentication)
    unregister_pre_processor(preproc_authorization)


def preproc_authentication(service, request, resource):
    """I make sure the user is authenticated, otherwise I prompt him to login."""
    session = request.environ['beaker.session']

    try:  # Succeed if the user has already been authenticated
        user_role = session['remote_user_role']

    except KeyError:  # User is not authenticated
        # If in the process of authenticating (redirect from Github or input from Basic Auth)
        authenticate(service, request)
        # Else, preproc_authorization() will be called afterward to invite the user to login

    except Exception, e:
        LOG.debug("An error occurred during authentication:\t{error_msg}".format(error_msg=e))

    else:  # If we manage to get the user role, we continue
        if user_role == 'admin' or user_role == 'user':
            request.remote_user = session['user_id']
            LOG.debug("User {0} is authenticated".format(request.remote_user))
        else:
            LOG.debug("User role should be 'user' or 'admin', got {user_role} instead. Re-doing authentication."
                      .format(user_role=user_role))
            authenticate(service, request)


def authenticate(service, request):
    """I authenticate a user, either via Github or via Basic Auth."""
    session = request.environ['beaker.session']

    def log_successful_auth(user_id):
        LOG.debug("User {0} has been successfully authenticated".format(user_id))

    # If the user IP is on the IP whitelist he must prove he has the admin credentials
    if request.remote_addr in IP_WHITELIST:
        auth = request.authorization

        # If the user has input the correct admin credentials, we log him in
        if auth and auth[0] == 'Basic' and auth[1] == ADMIN_CREDENTIALS_HASH:
            session['remote_user_role'] = 'admin'
            request.remote_user = session['user_id'] = request.remote_addr
            log_successful_auth(session['user_id'])

        # Else, the user has not yet input the credentials, or input the wrong ones so we prompt him again.
        else:
            raise UnauthorizedError()

    # If the user is being redirected by Github, we continue the Github auth flow
    elif request.GET.getall('code'):
        request.remote_user = session['user_id'] = github_flow(request)
        session['remote_user_role'] = 'user'
        log_successful_auth(session['user_id'])
        raise RedirectException(service.root_uri + session['user_id'] + '/')


def github_flow(request):
    """Github login flow after we receive a callback from Github.

    :return: User ID on Github
    """
    # 1. Exchange code for an access_token
    data = {
        'code': request.GET.getall('code')[0],
        'client_id': OAUTH_CONFIG['client_id'],
        'client_secret': OAUTH_CONFIG['client_secret']
    }
    enc_data = urllib.urlencode(data)
    gh_resp = urllib.urlopen(OAUTH_CONFIG['access_token_endpoint'], data=enc_data)
    gh_resp_qs = urlparse.parse_qs(gh_resp.read())
    access_token = gh_resp_qs[b'access_token'][0].decode('utf-8')

    # 2. Exchange access_token for user id.
    gh_resp_id = urllib.urlopen('{api_url}?access_token={at}'
                                .format(api_url=OAUTH_CONFIG['api_endpoint'], at=access_token))
    gh_resp_id = gh_resp_id.read().decode('utf-8')
    resp_id_dec = json.loads(gh_resp_id)

    return str(resp_id_dec['id'])


def preproc_authorization(service, request, resource):
    """I make sure the current user as the right to access the requested resource."""
    session = request.environ['beaker.session']

    # If the user is not authenticated, the access is forbidden: prompt him to login first
    try:  # This raises a KeyError if the user has not been authenticated yet
        role = session['remote_user_role']
    except KeyError:
        raise OAuth2Unauthorized(OAUTH_CONFIG['auth_endpoint'], OAUTH_CONFIG['client_id'], service.root_uri)

    # Else, the user is authenticated
    else:
        user_id = session['user_id']
        # If he wants to log out
        if "logout" in request.GET:
            session.delete()
            LOG.debug("User {0} has successfully logged out".format(user_id))
            raise UnauthorizedError("Successfully logged out", challenge="logged out")

        # Else, he is just browsing the kTBS:
        # If a user wants to do stuff on his base it's ok
        elif role == 'user' and request.path_info.startswith('/'+user_id+'/'):
            LOG.debug("User {user_id} is allowed to do a {method} request on <{res_uri}>."
                      .format(user_id=user_id, method=request.method, res_uri=request.path_info))
        # If a user wants to POST something on the root, it's ok
        elif role == 'user' and request.path_info == '/' and request.method == 'POST':
            LOG.debug("User {user_id} is allowed to POST on root <{root_uri}>."
                      .format(user_id=user_id, root_uri=service.root_uri))
        # If it's an admin, it's ok to do anything
        elif role == 'admin':
            LOG.debug("User {user_id} is allowed to do a {method} request on <{res_uri}> because he is an admin."
                      .format(user_id=user_id, method=request.method, res_uri=request.path_info))
        # Otherwise, the user is trying to access or post something at the wrong place
        else:
            LOG.debug("User {user_id} is forbidden to do a {method} request on <{res_uri}>"
                      .format(user_id=user_id, method=request.method, res_uri=request.path_info))
            raise AccessForbidden(redirect_uri=service.root_uri+user_id+'/')
