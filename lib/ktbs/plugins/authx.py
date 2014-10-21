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
This kTBS plugin provides authentication and authorization (hence authX).

It requires the following dependencies:

- beaker
- sqlalchemy (if you plan to use an SQL database to store sessions)
- if you use an SQL database and you use a database that is not SQLite:
  a driver library that provides bindings for your database type (e.g. psycopg2, mysqldb)

Authentication
--------------
We want to make sure the user is who he pretends he is.
At the end of the process we have an ID for the user.

There are two ways to authenticate :

- using an IP whitelist coupled with login/password credentials
- delegating it to an OAuth2 identity provider


Authorization
-------------
We check that the user has the rights to access a given resource.
A user has one of the two roles: *user* or *admin*.

If he has the role *user* then he can only access a base that has
his ID as name. He can also do POST request on the kTBS root.

If he has the role *admin* then he can do anything.


How to add a new OAuth2 identity provider (IP)?
-----------------------------------------------

- make a function that does the authentication flow between the IP and you.
  This function takes a request as argument and returns the unique user id
  given by the IP.

- declare this function in the dictionary ``registered_oauth_flows`` inside
  the function ``start_plugin``. The *key* you add to the dictionary is a
  string that represents the name of the IP, the *value* is the function object.

- add a section in the configuration file with the parameter you need for your flow.
  This section name MUST be the same as the key string you added to the dictionary.

"""

from rdfrest.http_server import \
    register_pre_processor, unregister_pre_processor, register_middleware, \
    UnauthorizedError, RedirectException, HttpException, \
    AUTHENTICATION, AUTHORIZATION, SESSION
from base64 import standard_b64encode
from logging import getLogger
from beaker.middleware import SessionMiddleware
from webob import Request
from ConfigParser import NoOptionError

import urllib
import json
import urlparse

LOG = getLogger(__name__)
OAUTH_CONFIG = None  # Dictionary for the OAuth2 configuration
IP_WHITELIST = []  # Set only if it exists in the configuration
ADMIN_CREDENTIALS_HASH = None  # Base64 hash of "login:password" if admin credentials are set in the configuration
SESSION_CONFIG = {}
ENABLE_BEAKER = None


class OAuth2Unauthorized(UnauthorizedError):

    """Prompt a user to login using an OAuth2 identity provider."""

    def __init__(self, auth_endpoint, redirect_uri, message="", **headers):
        """Set the information about the OAuth2 endpoint and redirect URI.

        We provide to the user the OAuth2 endpoint information using:
        - "Link" in the HTTP header
        - visual information in the HTML

        :param auth_endpoint: the OAuth2 authentication endpoint with parameter(s)
        :param redirect_uri: the URI to send the user back to after he logs in
        """
        self.auth_endpoint = auth_endpoint
        self.redirect_uri = redirect_uri
        self.headers = headers
        self.headers['Link'] = ['<{r_uri}>; rel=oauth_resource_server'
                                .format(r_uri=self.auth_endpoint),
                                '<{redirect_uri}>; rel=successful_login_redirect'
                                .format(redirect_uri=self.redirect_uri)]
        self.headers['Access-control-expose-headers'] = ['Link']
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
          <a href="{redirect_auth_uri}">Log in with OAuth2</a>.
          </body>
        </html>
        """.format(redirect_auth_uri=self.auth_endpoint)


class AccessForbidden(HttpException):

    """Tell a user that he has not the right to access the given resource.

    This typically arises when a user his logged in but tries to access
    a protected resource like the kTBS root or a base that doesn't belong
    to him.
    """

    def __init__(self, user_id, redirect_uri, root_uri, **headers):
        """I store information to render a useful 403 HTML page."""
        self.redirect_uri = redirect_uri
        self.user_id = user_id
        self.root_uri = root_uri
        self.headers = headers
        self.headers['Content-Type'] = "text/html"
        super(AccessForbidden, self).__init__(message="",
                                              status="403 Forbidden",
                                              **self.headers)

    def get_body(self):
        """I return the body of 403 page.

        This pages tell the user that he has not the right to access the resource.
        We check if his base exists. If so, we redirect him to his base, if not
        we invite him to create his base.

        .. note :: the '{{' and '}}' in the code bellow are meant
                   to escape '{' and '}' for the format method.
        """
        return """
            <!DOCTYPE html>
            <html>
            <head>
            <title>403 Forbidden</title>
            <meta charset="utf-8">
            </head>
            <body>
            <h1>403 Forbidden</h1>
            <p id="check_base">Checking if your base exists...</p>
            <script type="text/javascript">
            window.onload = function() {{

                var elemCheckBase = document.getElementById('check_base');

                // 1. Test if base exists
                var xhrBaseExists = new XMLHttpRequest();
                var status = null;
                xhrBaseExists.open("head", "{redirect_uri}", true);
                xhrBaseExists.onload = function () {{

                    if (xhrBaseExists.status == 200) {{ // 2. Base exists --> redirect user
                        elemCheckBase.innerHTML = "<a href='{redirect_uri}'>Your base</a> exists, redirecting in 5 s.";
                        setTimeout(function() {{window.location = "{redirect_uri}"}}, 5000);
                    }} else if (xhrBaseExists.status == 404) {{ // 3. Base doesn't exist --> invite to create base
                        elemCheckBase.innerHTML = "Your base doesn't exist. "+
                                                  "<a href='' id='create_base'>Create base?</a>";

                        var payloadCreateBase = '{{"@id": "{user_id}/","@type": "Base"}}';
                        document.getElementById('create_base').onclick = function() {{
                            // POST to create base.
                            var xhrCreateBase = new XMLHttpRequest();
                            xhrCreateBase.open("post", "{root_uri}", true);
                            xhrCreateBase.setRequestHeader('Content-Type', 'application/json');
                            xhrCreateBase.onload = function() {{
                                elemCheckBase.innerHTML = "<a href={redirect_uri}>Your base</a> has been created "+
                                    "(redirecting in 5 s).";
                                setTimeout(function() {{window.location = "{redirect_uri}"}}, 5000);
                            }}
                            xhrCreateBase.send(payloadCreateBase);
                            return false;
                        }};
                    }} else {{
                        elemCheckBase.innerHTML = "Didn't manage to see if your base exists.";
                    }}
                }}
                xhrBaseExists.send();
            }}
            </script>
            </body>
            </html>
            """.format(user_id=self.user_id,
                       redirect_uri=self.redirect_uri,
                       root_uri=self.root_uri)


class AuthSessionMiddleware(object):
    def __init__(self, app):
        self.session_config = {'session.auto': True,  # auto-save session
                               'session.key': 'sid'}
        self.session_config.update(SESSION_CONFIG)
        self.app = SessionMiddleware(app, self.session_config) if ENABLE_BEAKER else app

    def __call__(self, environ, start_response):
        req = Request(environ)
        resp = req.get_response(self.app)
        return resp(environ, start_response)


def start_plugin(_config):
    """I get the configuration values from the main kTBS configuration.

    .. note:: This function is called automatically by the kTBS.
              It is called once when the kTBS starts, not at each request.
    """
    registered_oauth_flows = {'oauth_github': github_flow,
                              'oauth_claco': claco_flow}

    def section_dict(section_name):
        """Convert a configuration section to a Python dictionary"""
        if _config.has_section(section_name):
            return {opt_key: opt_value for opt_key, opt_value in _config.items(section_name)}
        else:
            return None

    global OAUTH_CONFIG, IP_WHITELIST, ADMIN_CREDENTIALS_HASH, SESSION_CONFIG, ENABLE_BEAKER
    try:
        ENABLE_BEAKER = _config.getboolean('authx', 'enable_beaker')
    except NoOptionError:  # if we didn't set the `enable_beaker` option in the config, we set it to true by default
        ENABLE_BEAKER = True

    authx_config = section_dict('authx')

    # Session management
    session_config_keys = filter(lambda k: k.startswith('beaker.session.'), authx_config)
    SESSION_CONFIG = {k: authx_config[k] for k in session_config_keys}

    # Identity provider management
    ip_name = authx_config['oauth_flow']
    OAUTH_CONFIG = section_dict(ip_name)
    OAUTH_CONFIG['flow'] = registered_oauth_flows[ip_name]

    # Admin credentials management
    admin_auth_config = section_dict('authx_admin')
    if admin_auth_config:
        IP_WHITELIST = admin_auth_config['ip_whitelist'].split(' ')
        ADMIN_CREDENTIALS_HASH = standard_b64encode(admin_auth_config['login'] + ':' +
                                                    admin_auth_config['password'])

    register_middleware(SESSION, AuthSessionMiddleware)

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
        # If in the process of authenticating (redirect from OAuth2 identify provider or input from Basic Auth)
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
    """I authenticate a user, either via an OAuth2 identity provider or via Basic Auth."""
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

    # If the user is being redirected by the OAuth2 identity provider, we continue the auth flow
    elif request.GET.getall('code'):
        oauth_flow = OAUTH_CONFIG['flow']
        request.remote_user = session['user_id'] = oauth_flow(request)
        session['remote_user_role'] = 'user'
        log_successful_auth(session['user_id'])
        raise RedirectException(service.root_uri)


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


def claco_flow(request):
    # 1. Exchange code for an access_token
    claco_resp = urllib.urlopen(OAUTH_CONFIG['access_token_endpoint']+'&code='+request.GET.getall('code')[0])
    claco_resp_access_token = claco_resp.read().decode('utf-8')
    access_token = json.loads(claco_resp_access_token)['access_token']

    # 2. Exchange access_token for user id.
    claco_resp_id = urllib.urlopen('{api_url}?access_token={at}'
                                   .format(api_url=OAUTH_CONFIG['api_endpoint'], at=access_token))
    claco_resp_id = claco_resp_id.read().decode('utf-8')
    resp_id_dec = json.loads(claco_resp_id)

    return str(resp_id_dec['user_id'])


def preproc_authorization(service, request, resource):
    """I make sure the current user as the right to access the requested resource."""
    session = request.environ['beaker.session']

    # If the user is not authenticated, the access is forbidden: prompt him to login first
    try:  # This raises a KeyError if the user has not been authenticated yet
        role = session['remote_user_role']
    except KeyError:
        raise OAuth2Unauthorized(OAUTH_CONFIG['auth_endpoint'], service.root_uri)

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
            raise AccessForbidden(user_id=user_id,
                                  redirect_uri=service.root_uri+user_id+'/',
                                  root_uri=service.root_uri)
