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
This is a standalone version of an HTTP-based KTBS.
"""
import atexit
import logging
from optparse import OptionParser, OptionGroup
from rdfrest.http_server import SparqlHttpFrontend
from rdfrest.serializers import bind_prefix, get_prefix_bindings
from .config import get_ktbs_configuration
from socket import getaddrinfo, AF_INET6, AF_INET, SOCK_STREAM
from wsgiref.simple_server import WSGIServer, make_server

from .namespace import KTBS
from .engine.service import KtbsService
from .utils import SKOS

OPTIONS = None
LOG = logging.getLogger("ktbs")

def main():
    """I launch KTBS as a standalone HTTP server.
    """
    global OPTIONS # global statement #pylint: disable=W0603
    OPTIONS = parse_options()

    # Get default configuration possibly overriden by a user configuration file
    # or command line configuration OPTIONS
    ktbs_config = parse_configuration_options()

    log_level = ktbs_config.get('debug', 'log-level', 1).upper()
    logging.basicConfig(level=log_level) # configure logging

    for plugin_name in ktbs_config.options('plugins'):
        if ktbs_config.getboolean('plugins', plugin_name):
            try:
                plugin = __import__(plugin_name, fromlist="start_plugin")
            except ImportError:
                plugin = __import__("ktbs.plugins." + plugin_name,
                                    fromlist="start_plugin")
            plugin.start_plugin()

    # TODO : remove this option ?
    if ktbs_config.getboolean('server', 'resource-cache'):
        LOG.warning("option --resource-cache is deprecated; it has no effect")

    ktbs_service = KtbsService(ktbs_config)  #.service
    atexit.register(lambda: ktbs_service.store.close())

    application = SparqlHttpFrontend(ktbs_service, ktbs_config)

    if ktbs_config.getboolean('server', 'flash-allow'):
        application = FlashAllower(application)

    for prefix, uri in ktbs_config.items('ns_prefix'):
        bind_prefix(prefix, uri)

    httpd = make_server(ktbs_config.get('server', 'host-name', 1),
                        ktbs_config.getint('server', 'port'),
                        application,
                        make_server_class(ktbs_config))

    LOG.info("KTBS server at %s" % ktbs_service.root_uri)
    requests = ktbs_config.getint('debug', 'requests')
    if requests == -1:
        httpd.serve_forever()
    else:
        while requests:
            httpd.handle_request()
            requests -= 1

def parse_configuration_options():
    """I get kTBS default configuration options and override them with
    command line options.

    Command line options are stored in a global variable.
    If this changes, it should be passed as a parameter to this function.

    :return: Configuration object.
    """
    config = get_ktbs_configuration(OPTIONS.configfile)

    # Override default / config file parameters with command line parameters
    if OPTIONS.host_name is not None:
        config.set('server', 'host-name', OPTIONS.host_name)

    if OPTIONS.port is not None:
        config.set('server', 'port', str(OPTIONS.port))

    if OPTIONS.base_path is not None:
        config.set('server', 'base-path', OPTIONS.base_path)

    if OPTIONS.repository is not None:
        config.set('rdf_database', 'repository', OPTIONS.repository)

    if OPTIONS.ns_prefix is not None:
        for nsprefix in OPTIONS.ns_prefix:
            prefix, uri = nsprefix.split(':', 1)
            config.set('ns_prefix', prefix, uri)

    if OPTIONS.plugin is not None:
        for plugin in  OPTIONS.plugin:
            # TODO - do we code an else (third party plugins possible) ?
            if config.has_option('plugins', plugin):
                config.set('plugins', plugin, 'true')

    if OPTIONS.force_ipv4 is not None:
        config.set('server', 'force-ipv4', 'true')

    if OPTIONS.max_bytes is not None:
        # TODO max_bytes us not defined as an int value in OptionParser ?
        config.set('server', 'max-bytes', OPTIONS.max_bytes)

    if OPTIONS.no_cache is not None:
        config.set('server', 'no-cache', 'true')

    if OPTIONS.flash_allow is not None:
        config.set('server', 'flash-allow', 'true')

    if OPTIONS.max_triples is not None:
        config.set('server', 'max-triples', str(OPTIONS.max_triples))

    if OPTIONS.cors_allow_origin is not None:
        config.set('server', 'cors-allow-origin', str(OPTIONS.cors_allow_origin))

    if OPTIONS.force_init is not None:
        config.set('rdf_database', 'force-init', 'true')

    if OPTIONS.resource_cache is not None:
        #config.set('server', 'resource-cache', OPTIONS.resource_cache)
        config.set('server', 'resource-cache', 'true')

    if OPTIONS.log_level is not None:
        config.set('debug', 'log-level', str(OPTIONS.log_level))

    if OPTIONS.requests is not None:
        # TODO How to manage -1 = -R1, -2 = -R2
        config.set('debug', 'requests', str(OPTIONS.requests))

    return config

def parse_options():
    """I parse sys.argv for the main.
    """
    opt = OptionParser(description="HTTP-based Kernel for Trace-Based Systems")
    opt.add_option("-H", "--host-name") #, default="localhost")
    opt.add_option("-p", "--port", type=int) #default=8001, type=int)
    opt.add_option("-b", "--base-path") #, default="")
    opt.add_option("-r", "--repository",
                  help="the filename/identifier of the RDF database (default: "
                       "in memory)")
    opt.add_option("-c", "--configfile")
    opt.add_option("-n", "--ns-prefix", action="append",
                  help="a namespace prefix declaration as 'prefix:uri'")
    opt.add_option("-P", "--plugin", action="append",
                  help="loads the given plugin")

    ogr = OptionGroup(opt, "Advanced options")
    ogr.add_option("-4", "--force-ipv4", action="store_true", #default=False,
                   help="Force IPv4")
    ogr.add_option("-B", "--max-bytes",
                   help="sets the maximum number of bytes of payloads"
                   "(no limit if unset)")
    ogr.add_option("-N", "--no-cache", type=int, #default=0,
                   help="prevent kTBS to send cache-control directives")
    ogr.add_option("-F", "--flash-allow", action="store_true",
                   help="serve a policy file allowing Flash applets to connect")
    ogr.add_option("-T", "--max-triples",
                   help="sets the maximum number of bytes of payloads"
                   "(no limit if unset)")
    ogr.add_option("--cors-allow-origin",
                   help="space separated list of allowed origins")
    ogr.add_option("--force-init", action="store_true", #default=None,
                   help="Force initialization of repository (assumes -r)")
    opt.add_option_group(ogr)

    ogr = OptionGroup(opt, "Deprecated options")
    ogr.add_option("--resource-cache", action="store",
                   help="not used anymore")
    opt.add_option_group(ogr)
    
    ogr = OptionGroup(opt, "Debug options")
    ogr.add_option("-l", "--log-level", #default="info",
                   choices=["debug", "info", "warning", "error", "critical"],
                   help="specify the debug level (debug, info, warning, error, critical)")
    ogr.add_option("-R", "--requests", type=int, #default=-1,
                   help="serve only the given number of requests")
    ogr.add_option("-1", "--once", action="callback", callback=number_callback,
                   help="serve only one query (equivalent to -R1)")
    ogr.add_option("-2", action="callback", callback=number_callback,
                   help="serve only one query (equivalent to -R2)")
    opt.add_option_group(ogr)

    options, args = opt.parse_args()
    if args:
        opt.error("spurious arguments")
    return options
    

def number_callback(_option, opt, _value, parser):
    """I manage options -R, -1 and -2"""
    val = int(opt[1:])
    parser.values.requests = val


def make_server_class(ktbs_config):
    """We define this closure so that MyWSGIServer class
       can access the configuration options.
    """

    class MyWSGIServer(WSGIServer):
        """
        I override WSGIServer to make it possibly IPV6-able.
        """
        def __init__(self, (host, port), handler_class):
            ipv = self.address_family = AF_INET
            if ktbs_config.get('server', 'force-ipv4', 1):
                info = getaddrinfo(host, port, AF_INET, SOCK_STREAM)
            else:
                info = getaddrinfo(host, port, 0, SOCK_STREAM)
                # when IPV6 is available, prefer it to IPV4
                if [ i for i in info if i[0] == AF_INET6 ]:
                    ipv = self.address_family =  AF_INET6
            LOG.info("Using IPV%s" % {AF_INET: 4, AF_INET6: 6}[ipv])
            WSGIServer.__init__(self, (host, port), handler_class)
    return MyWSGIServer

class NoCache(object):
    """
    A strawman cache doing no real caching, used for debugging.
    """
    # too few public methods #pylint: disable=R0903
    @staticmethod
    def get(_key):
        "Always return None"
        return None
    def __setitem__(self, key, name):
        "Do not really store the item."
        pass

class FlashAllower(object):
    """
    I wrap a WSGI application in order to make it accessible to Flash applets.

    This is done by serving /crossdomain.xml .
    """
    #pylint: disable-msg=R0903
    #    too few public methods

    def __init__(self, app, *domains):
        """
        * app: the wrapped WSGI application
        * domains: a list of allowed domains (if empty, '*' is assumed)
        """
        if not domains:
            domains = ["*"]
        allow = [ '<allow-access-from domain="%s"/>' % i for i in domains ]
        self.xml = xml = (
           '<?xml version="1.0"?>\n'
           '<!DOCTYPE cross-domain-policy SYSTEM '
           '"http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">\n'
           '<cross-domain-policy>\n%s\n</cross-domain-policy>\n'
        ) % "\n".join(allow)
        self.size = str(len(xml))
        self.app = app

    def __call__(self, env, start_response):
        if env["PATH_INFO"] == "/crossdomain.xml":
            start_response("200 OK", [
              ("content-type", "application/xml"),
              ("content-size", self.size),
            ])
            return [self.xml]
        else:
            return self.app(env, start_response)
