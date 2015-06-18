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
from socket import getaddrinfo, AF_INET6, AF_INET, SOCK_STREAM
from wsgiref.simple_server import WSGIServer, make_server

from rdfrest.util.config import apply_global_config
from rdfrest.http_server import HttpFrontend
from .config import get_ktbs_configuration

from os import getpid

#from .namespace import KTBS
from .engine.service import KtbsService

LOG = logging.getLogger("ktbs")

def main():
    """I launch KTBS as a standalone HTTP server.
    """
    cmdline_options = parse_options()

    # Get default configuration possibly overriden by a user configuration file
    # or command line configuration OPTIONS
    ktbs_config = parse_configuration_options(cmdline_options)

    # TODO : remove this option ?
    if ktbs_config.getboolean('server', 'resource-cache'):
        LOG.warning("option --resource-cache is deprecated; it has no effect")

    ktbs_config.set("logging", "loggers", "rdfrest ktbs");
    apply_global_config(ktbs_config)

    LOG.info("KTBS pid: %d" % getpid())

    ktbs_service = KtbsService(ktbs_config)  #.service
    atexit.register(lambda: ktbs_service.store.close())

    application = HttpFrontend(ktbs_service, ktbs_config)

    if ktbs_config.getboolean('server', 'flash-allow'):
        application = FlashAllower(application)

    httpd = make_server(ktbs_config.get('server', 'host-name', 1),
                        ktbs_config.getint('server', 'port'),
                        application,
                        make_server_class(ktbs_config))

    LOG.info("KTBS server at %s" % ktbs_service.root_uri)

    httpd.serve_forever()

def parse_configuration_options(options=None):
    """I get kTBS default configuration options and override them with
    command line options.

    :param options: Command line options.

    :return: Configuration object.
    """

    config = None

    if options is None or options.configfile is None:
        config = get_ktbs_configuration()
    else:
        #if options is not None and options.configfile is not None:
        if options.configfile is not None:
            with open(options.configfile) as configfile_handler:
                config = get_ktbs_configuration(configfile_handler)

    if options is not None and config is not None:
        # Override default / config file parameters with command line parameters
        if options.host_name is not None:
            config.set('server', 'host-name', options.host_name)

        if options.port is not None:
            config.set('server', 'port', str(options.port))

        if options.base_path is not None:
            config.set('server', 'base-path', options.base_path)

        if options.repository is not None:
            config.set('rdf_database', 'repository', options.repository)

        if options.ns_prefix is not None:
            for nsprefix in options.ns_prefix:
                prefix, uri = nsprefix.split(':', 1)
                config.set('ns_prefix', prefix, uri)
                
        if options.plugin is not None:
            for plugin in options.plugin:
                config.set('plugins', plugin, 'true')

        if options.force_ipv4 is not None:
            config.set('server', 'force-ipv4', 'true')

        if options.max_bytes is not None:
            # TODO max_bytes us not defined as an int value in OptionParser ?
            config.set('server', 'max-bytes', options.max_bytes)

        if options.no_cache is not None:
            config.set('server', 'no-cache', 'true')

        if options.flash_allow is not None:
            config.set('server', 'flash-allow', 'true')

        if options.max_triples is not None:
            config.set('server', 'max-triples', str(options.max_triples))

        if options.cors_allow_origin is not None:
            if "cors" not in config.sections():
                config.add_section("cors")
            config.set('cors', 'allow-origin', str(options.cors_allow_origin))

        if options.force_init is not None:
            config.set('rdf_database', 'force-init', 'true')

        if options.resource_cache is not None:
            #config.set('server', 'resource-cache', options.resource_cache)
            config.set('server', 'resource-cache', 'true')

        if options.loggers is not None:
            config.set('logging', 'loggers', str(options.loggers))

        if options.loggers is not None:
            config.set('logging', 'loggers', ' '.join(options.loggers))

        if options.console_level is not None:
            config.set('logging', 'console-level', str(options.console_level))

        if options.file_level is not None:
            config.set('logging', 'file-level', str(options.file_level))

        if options.logging_filename is not None:
            config.set('logging', 'filename', str(options.logging_filename))

    return config

def build_cmdline_options():
    """I build ktbs command line options."""

    opt = OptionParser(description="HTTP-based Kernel for Trace-Based Systems")
    opt.add_option("-H", "--host-name")
    opt.add_option("-p", "--port")
    opt.add_option("-b", "--base-path")
    opt.add_option("-r", "--repository",
                  help="the filename/identifier of the RDF database (default: "
                       "in memory)")
    opt.add_option("-c", "--configfile")
    opt.add_option("-n", "--ns-prefix", action="append",
                  help="a namespace prefix declaration as 'prefix:uri'")
    opt.add_option("-P", "--plugin", action="append",
                  help="loads the given plugin")

    ogr = OptionGroup(opt, "Advanced options")
    ogr.add_option("-4", "--force-ipv4", action="store_true",
                   help="Force IPv4")
    ogr.add_option("-B", "--max-bytes",
                   help="sets the maximum number of bytes of payloads"
                   "(no limit if unset)")
    ogr.add_option("-N", "--no-cache", action="store_true",
                   help="prevent kTBS to send cache-control directives")
    ogr.add_option("-F", "--flash-allow", action="store_true",
                   help="serve a policy file allowing Flash applets to connect")
    ogr.add_option("-T", "--max-triples",
                   help="sets the maximum number of bytes of payloads"
                   "(no limit if unset)")
    ogr.add_option("--cors-allow-origin",
                   help="space separated list of allowed origins (requires the cors plugin)")
    ogr.add_option("--force-init", action="store_true",
                   help="Force initialization of repository (assumes -r)")
    opt.add_option_group(ogr)

    ogr = OptionGroup(opt, "Deprecated options")
    ogr.add_option("--resource-cache", action="store",
                   help="not used anymore")
    opt.add_option_group(ogr)
    
    ogr = OptionGroup(opt, "Logging options")
    ogr.add_option("--loggers", action="append",
                   help="for which module(s), you want to activate logging (ktbs, rdfrest, rdflib, ...)")

    ogr.add_option("--console-level", 
                   choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                   help="specify the logging level for the console (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    ogr.add_option("--file-level", 
                   choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                   help="specify the logging level for the logging file (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    ogr.add_option("--logging-filename",
                   help="specify the filename for the logging file")
    ogr.add_option("-1", "--once", action="callback", callback=number_callback,
                   help="serve only one query (equivalent to -R1)")
    ogr.add_option("-2", action="callback", callback=number_callback,
                   help="serve only one query (equivalent to -R2)")
    opt.add_option_group(ogr)

    return opt


def parse_options():
    """I parse sys.argv for the main.
    """

    opt = build_cmdline_options()

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
