#!/usr/bin/env python
#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
from logging import basicConfig
from optparse import OptionParser, OptionGroup
from rdflib import plugin as rdflib_plugin
from rdflib.store import Store
from socket import getaddrinfo, AF_INET6, AF_INET, SOCK_STREAM
from sys import stderr
from wsgiref.simple_server import WSGIServer, make_server

from rdfrest.http_front import HttpFrontend
from ktbs.namespaces import KTBS, SKOS
from ktbs.local.service import KtbsService

OPTIONS = None

def main():
    """I launch KTBS as a standalone HTTP server.
    """
    global OPTIONS # global statement #pylint: disable=W0603
    OPTIONS = parse_options()
    for plugin in OPTIONS.plugin or ():
        __import__(plugin)
    basicConfig() # configure logging
    uri = "http://%(host_name)s:%(port)s%(base_path)s/" % OPTIONS.__dict__
    cache_control = None
    if OPTIONS.max_age:
        cache_control = lambda *r: "max-age=%d" % OPTIONS.max_age
    repository = OPTIONS.repository
    if not repository.startswith(":"):
        repository = ":Sleepycat:%s" % repository
    _, store_type, config_str = repository.split(":", 2)
    store = rdflib_plugin.get(store_type, Store)(config_str)
    ktbs_service = KtbsService(store, uri)
    if OPTIONS.resource_cache == "none":
        ktbs_service._resource_cache = NoCache()
    elif OPTIONS.resource_cache == "aggressive":
        ktbs_service._resource_cache = {}
    application = HttpFrontend(ktbs_service, cache_control=cache_control)
    application.serializers.bind_prefix("skos", SKOS)
    for nsprefix in OPTIONS.ns_prefix or ():
        prefix, uri = nsprefix.split(1)
        application.serializers.bind_prefix(prefix, uri)
    for prefix in ["", "k", "ktbs", "ktbsns"]:
        if prefix not in application.serializers.namespaces:
            application.serializers.bind_prefix(prefix, KTBS)
            break
    if OPTIONS.flash_allow:
        application = FlashAllower(application)

    httpd = make_server(OPTIONS.host_name, OPTIONS.port, application,
                        MyWSGIServer)
    print >> stderr, "KTBS server at %s" % uri
    requests = OPTIONS.requests
    if requests == -1:
        httpd.serve_forever()
    else:
        while requests:
            httpd.handle_request()
            requests -= 1


def parse_options():
    """I parse sys.argv for the main.
    """
    opt = OptionParser(description="HTTP-based Kernel for Trace-Based Systems")
    opt.add_option("-H", "--host-name", default="localhost")
    opt.add_option("-p", "--port", default=8001, type=int)
    opt.add_option("-b", "--base-path", default="")
    opt.add_option("-r", "--repository", default=":IOMemory:",
                  help="the filename of the RDF database (default: in memory)")
    opt.add_option("-n", "--ns-prefix", action="append",
                  help="a namespace prefix declaration as 'prefix:uri'")
    opt.add_option("-P", "--plugin", action="append",
                  help="loads the given plugin")

    oga = OptionGroup(opt, "Advanced OPTIONS")
    oga.add_option("-4", "--ipv4", action="store_true", default=False,
                   help="Force IPv4")
    oga.add_option("-A", "--max-age", default=0, type=int,
                   help="the cache duration (in seconds) of contents served by "
                   " the kTBS")
    oga.add_option("-F", "--flash-allow", action="store_true",
                   help="serve a policy file allowing Flash applets to connect")
    opt.add_option_group(oga)

    ogd = OptionGroup(opt, "Debug OPTIONS")
    ogd.add_option("--resource-cache", action="store", default="default",
                   choices=["none", "default", "aggressive"], 
                   help="sets the kind of resource cache")
    ogd.add_option("-R", "--requests", type=int, default=-1,
                   help="serve only the given number of requests")
    ogd.add_option("-1", "--once", action="callback", callback=number_callback,
                   help="serve only one query (equivalent to -R1)")
    ogd.add_option("-2", action="callback", callback=number_callback,
                   help="serve only one query (equivalent to -R2)")
    opt.add_option_group(ogd)

    options, args = opt.parse_args()
    if args:
        opt.error("spurious arguments")
    return options
    

def number_callback(_option, opt, _value, parser):
    """I manage OPTIONS -R, -1 and -2"""
    val = int(opt[1:])
    parser.values.requests = val


# We define MyWSGIServer here, so that it can access OPTIONS
class MyWSGIServer(WSGIServer):
    """
    I override WSGIServer to make it possibly IPV6-able.
    """
    def __init__(self, (host, port), handler_class):
        ipv = self.address_family = AF_INET
        if OPTIONS.ipv4:
            info = getaddrinfo(host, port, AF_INET, SOCK_STREAM)
        else:
            info = getaddrinfo(host, port, 0, SOCK_STREAM)
            # when IPV6 is available, prefer it to IPV4
            if [ i for i in info if i[0] == AF_INET6 ]:
                ipv = self.address_family =  AF_INET6
        print >> stderr, "===", "Using IPV%s" % {AF_INET: 4, AF_INET6: 6}[ipv]
        WSGIServer.__init__(self, (host, port), handler_class)

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
