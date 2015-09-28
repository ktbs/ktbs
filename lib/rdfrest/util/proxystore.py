# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011 Françoise Conil <francoise.conil@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    RDF-REST is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RDF-REST is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with RDF-REST.  If not, see <http://www.gnu.org/licenses/>.

"""
I implement an rdflib store that acts as a proxy to a RESTful RDF graph.
"""

import httplib
import httplib2
from StringIO import StringIO
import types

#http://docs.python.org/howto/logging-cookbook.html
import logging
LOG = logging.getLogger(__name__)

from rdflib.store import Store, VALID_STORE
  #, CORRUPTED_STORE, NO_STORE, UNKNOWN
from rdflib.graph import Graph
#from rdflib.term import URIRef

# TODO LATER decide which parser/serializer infrastructure to use
# for the moment, we use rdflib plugins; we could switch to rdfrest
# advantage of rdflib:
#  * makes proxystore usable outside rdfrest
#  * all formats manages by rdflib allow roundtrip,
#    while rdfrest may have serializers without a parser, on conversly
# advantages of rdfrest:
#  * could use formats not supported by rdflib (JSON-LD?)

# TODO LATER We should scan rdflib registered parsers : rdflib/plugin.py
#      rdflib has a turtle serializer but no turtle parser
#from rdflib.parser import Parser
#from rdflib.serializer import Serializer
#from rdflib.plugin import plugins

_CONTENT_TYPE_PARSERS = {}
_CONTENT_TYPE_SERIALIZERS = {}

FORMAT_N3   = "n3"
FORMAT_XML  = "xml"
FORMAT_RDFA = "rdfa"
FORMAT_NT   = "nt"
FORMAT_TRIX = "trix"

PS_CONFIG_URI = "uri"
PS_CONFIG_HTTP_CX = "httpcx"
PS_CONFIG_HTTP_RESPONSE = "httpresponse"
PS_CONFIG_DEBUG_HTTP = "debughttp"

# TODO LATER generate accept based on available parsers?

ACCEPT = ",".join( ";q=".join(pair) for pair in [
        ("text/nt",             "1"),
        ("text/turtle",         "0.8"),
        ("application/rdf+xml", "0.6"),
])

def _get_rdflib_parsers():
    """ Try to get rdflib registered Parsers.
        TODO LATER can we make an automatic match Content-Type / rdflib parser ?
    """
    # parsers = plugins(name=None, kind=Parser) ## parsers in not used
    # lp = [ p.name for p in parsers ] ## lp is not used
    # ['n3', 'trix', 'xml', 'application/xhtml+xml', 'text/html', 'nt',  
    #  'application/rdf+xml', 'rdfa']

    # rdflib
    _CONTENT_TYPE_PARSERS["text/rdf+n3"] = FORMAT_N3
    # http://www.w3.org/TeamSubmission/turtle/
    _CONTENT_TYPE_PARSERS["text/turtle"] = FORMAT_N3
    # A accepter car historique
    _CONTENT_TYPE_PARSERS["application/x-turtle"] = FORMAT_N3
    # Acceptés par KTBS
    _CONTENT_TYPE_PARSERS["text/x-turtle"] = FORMAT_N3
    _CONTENT_TYPE_PARSERS["application/turtle"] = FORMAT_N3

    _CONTENT_TYPE_PARSERS["application/rdf+xml"] = "xml"#"application/rdf+xml"
    _CONTENT_TYPE_PARSERS["text/nt"] = FORMAT_NT # seems to be more efficient
    _CONTENT_TYPE_PARSERS["text/plain"] = FORMAT_NT # seems to be more efficient

def _get_rdflib_serializers():
    """ Try to get rdflib registered Serializers.
        TODO LATER Automate ?
    """
    _CONTENT_TYPE_SERIALIZERS[FORMAT_N3] = "text/turtle"
    _CONTENT_TYPE_SERIALIZERS[FORMAT_NT] = "text/nt"
    _CONTENT_TYPE_SERIALIZERS[FORMAT_XML] = "application/rdf+xml"

# Build rdflib parsers list from content-type
_get_rdflib_parsers()

# Build rdflib serializers list 
_get_rdflib_serializers()

class ProxyStore(Store):
    """
    A Proxy store implemention.

   :param configuration: Can be a string or a dictionary. May be 
        passed to __init__() or to open(). Specified as a
        configuration string (store database connection string). For
        KTBS, it is preferably a dictionary which may contain
        credentials for HTTP requests, the URI of the graph and an
        httpresponse supplied by the client (contains an RDF
        serialized graph already posted with HTTPLIB2 and the header
        of the response). If the parameters are in a string, the
        format should be "key1:value1;key2:value2".  May be passed to
        __init__() or to open().  Optionnal.

    :param identifier:
        URIRef identifying the graph to cache in the store.

    See http://www.rdflib.net/store/ for the detail of a store.
    Take store.py for the squeletton.

    The real store is on a server accessed with a REST protocol.
    """

    # Already define in the Store class
    context_aware = False
    formula_aware = False
    transaction_aware = False

    def __init__(self, configuration=None, identifier=None):
        """ ProxyStore initialization.

            Creates an empty Graph, intializes the HTTP client.
            Use the defaut for internal graph storage, i.e IOMemory.
            The URIref of the graph must be supplied either in identifier or
            in configuration parameter. It will be checked by open().
            The cache file path could be given in the configuration dictionary
            (__init__ only). We have to search about the memory cache.
        """

        LOG.debug("-- ProxyStore.init(configuration=%s, identifer=%s) --\n",
                  configuration, identifier)


        self._identifier = identifier
        self._format = None
        self._etags = None
        self._req_headers = {}

        self.configuration = None
        configuration = self._configuration_extraction(configuration)

        self._graph = Graph()

        # Most important parameter : identifier and graph address
        # If not given, we can not go further
        if (identifier is not None) and len(identifier) > 0:
            if len(configuration) == 0:
                configuration = {PS_CONFIG_URI: identifier}

        # Show the network activity
        if PS_CONFIG_DEBUG_HTTP in configuration.keys():
            httplib2.debuglevel = 1

        # Use provided Http connection if any
        http_cx = configuration.get(PS_CONFIG_HTTP_CX)
        if http_cx is None:
            http_cx = httplib2.Http()
        else:
            assert isinstance(http_cx, httplib2.Http)
        self.httpserver = http_cx

        # Store will call open() if configuration is not None
        Store.__init__(self, configuration)

    @property
    def prefered_format(self):
        """The format that the remote server seems to prefer.

        Return a tuple (content_type, rdflib_format)
        """
        return _CONTENT_TYPE_SERIALIZERS.get(self._format, "text/turtle"), \
               (self._format or "turtle")

    def open(self, configuration, create=False):
        """ Opens the store specified by the configuration string. 
            For the ProxyStore, the identifier is the graph address.

            :param configuration: Usually a configuration string of the store 
                (for database connection). May contain credentials for HTTP 
                requests. Can be a string or a dictionary. May be passed to 
                __init__() or to open(). 
            :param create: True to create a store. This not meaningfull for the
                ProxyStore. Optionnal.


            :returns: * VALID_STORE on success
                      * UNKNOWN No identifier or wrong identifier
                      * NO_STORE
        """
        LOG.debug("-- ProxyStore.open(configuration=%s, create=%s), "
                  "identifier: %s --\n",
                  configuration, create, self._identifier)

        self.configuration = self._configuration_extraction(configuration)

        if (self._identifier is None) or len(self._identifier) == 0:
            if PS_CONFIG_URI in self.configuration.keys():
                self._identifier = self.configuration[PS_CONFIG_URI]
            else:
                raise StoreIdentifierError(identifier=self._identifier)
        else:
            if (PS_CONFIG_URI in self.configuration.keys()) and \
               (self._identifier != self.configuration[PS_CONFIG_URI]):
                raise StoreIdentifierError(identifier=self._identifier)

        if PS_CONFIG_HTTP_RESPONSE in self.configuration.keys():
            # Serialized graph already sent by the client to the server
            # Populated the graph with the server response, no need to pull
            # the data from the server again
            if len(self.configuration[PS_CONFIG_HTTP_RESPONSE]) == 2:
                self._parse_header(\
                        self.configuration[PS_CONFIG_HTTP_RESPONSE][0])
                self._parse_content(\
                        self.configuration[PS_CONFIG_HTTP_RESPONSE][1])

        return VALID_STORE

    @staticmethod
    def _configuration_extraction(configuration):
        """ Extract configuration data passed to ProxyStore.

            What do we do if configuration is passed twice (once in __init__
            and again in open) ? For the moment, overwrite.

            For the moment, ignore invalid configuration parameters (no
            StoreInvalidConfigurationError exception).

            :param configuration: Usually a configuration string of the store 
                (for database connection). May contain credentials for HTTP 
                requests. Can be a string or a dictionary. May be passed to 
                __init__() or to open(). Optionnal.

            :returns: A dictionnary with the extracted configuration.
        """

        extracted_configuration = {}
        
        # TODO LATER ? if self.configuration is not None:
        if isinstance(configuration, types.DictType):
            extracted_configuration = configuration

        elif isinstance(configuration, types.StringTypes):

            if len(configuration) > 0:

                # Expect to get a key1:value1;key2:value2;.... string
                # If not formatted like this, nothing should be extracted
                for item in configuration.split(";"):
                    elems = item.split(":")

                    if len(elems) == 2:
                        extracted_configuration[elems[0]] = elems[1]

        return extracted_configuration

    def _parse_header(self, header):
        """ Parses the header of the HTTP request or response.
            TODO LATER Analyse Content-Type HTTP header to determine
                 the serialization used
            TODO LATER The serialization must be stored

            :param header: Header of the HTTP request or response.
        """
        ctype = header.get("content-type", "text/turtle").split(";", 1)[0]
        self._format = _CONTENT_TYPE_PARSERS[ctype]

        LOG.debug("-- ProxyStore._parse_header(), "
                  "content-type=%s, self._format=%s --",
                  ctype, self._format)

        self._etags = header.get('etag')

    def _parse_content(self, content):
        """ Parses the data in the content parameter to build the graph to 
            cache.

            :param content: HTTP received data either got by ProxyStore or
                passed by RDFREST Client.
        """
        # Creates the graph
        LOG.debug("-- ProxyStore._parse_content() using %s format", 
                  self._format)

        parse_format = self._format
        if parse_format == "nt":
            parse_format = "n3" # seems to be more efficient!...
        self.remove((None, None, None), None) # efficiently empties graph
        # the above is much faster than remove((None, None, None))
        self._graph.parse(StringIO(content), format=self._format,
                          publicID=self._identifier)

    def _pull(self):
        """Update cache before an operation.
           This method must be called before each get-type request.
        """
        LOG.debug("-- _pull ... start ...")

        assert self._identifier is not None, "The store must be open."

        # TODO SOON - If there is a problem to get the graph (wrong address...)
        # Set an indication to notify it
        req_headers = {
            "accept": ACCEPT,
            }

        req_headers.update(self._req_headers)

        self._req_headers.clear()

        header, content = self.httpserver.request(self._identifier,
                                                  headers=req_headers)
        LOG.debug("[received header]\n%s", header)

        # TODO SOON Refine, test and define use-cases
        # httplib2 raises a httplib2.ServerNotFoundError exception when ...
        # Throw a ResourceAccessError exception in case of HTTP 404 as we have
        # no better mean at the moment
        if header.status == httplib.NOT_FOUND:
            raise ResourceAccessError(header.status, self._identifier,
                                      self.configuration)

        if not header.fromcache or self._format is None:
            LOG.debug("[received content]\n%s", content)

            if self._format is None:
                LOG.debug("Creating proxy graph  ....")
            else:
                LOG.debug("Updating proxy graph  ....")

            self._parse_header(header)
            self._parse_content(content)
            
        else:
            LOG.debug("Proxy graph is up to date ...")

        LOG.debug("-- _pull() ... stop ...")

    def force_refresh(self, clear_cache=False):
        """Forces the cache to be updated with HTTP specific headers.

        If `clear_cache` is False (default),
        etags will still be used, so the server may reply with a 304 Not Changed.
        If `clear_cache` is True,
        the cache will be cleared, so the content will have to be resent by the server.
        """
        LOG.debug("-- force_refresh called ()")

        if clear_cache:
            self._req_headers = {
                "Cache-Control" : "no-cache",
                }
        else:
            self._req_headers = {
                "Cache-Control" : "max-age=0",
                }

    def _push(self):
        """ Send data to server.
            Apply the modifications on the cache, trigger an exception if data
            has already been modified on the server.
        """
        LOG.debug("-- _push() ... start ... --")

        assert self._identifier is not None, "The store must be open."

        # TODO SOON : How to build the "PUT" request ?
        # Which data in the header ? 
        # Which serialization ? The same as we received but does rdflib supply
        # all kind of parsing / serialization ?
        headers = {'Content-Type': '%s; charset=UTF-8'
                   % _CONTENT_TYPE_SERIALIZERS[self._format],
                   'Accept': ACCEPT,
                   }
        if self._etags:
            headers['If-Match'] = self._etags
        data = self._graph.serialize(format=self._format)

        LOG.debug("[sent headers]\n%s", headers)
        LOG.debug("[sent data]\n%s", data)

        # TODO SOON : Analyze the server response
        #        The server will tell if the graph has changed
        #        The server will supply new ETags ... update the data with the
        # response
        rheader, rcontent = self.httpserver.request(self._identifier,
                                                    'PUT',
                                                    data,
                                                    headers=headers)

        LOG.debug("[response header]\n%s", rheader)
        LOG.debug("[response content]\n%s", rcontent)

        if rheader.status in (httplib.OK,):
            self._parse_header(rheader)
        elif rheader.status in (httplib.PRECONDITION_FAILED,):
            raise GraphChangedError(url=self._identifier, msg=rheader.status)
        elif str(rheader.status)[0] == "5":
            raise ServerError(url=self._identifier, msg=rheader.status)
        else:
            raise RuntimeError("%s: %s %s\n%s" % (self._identifier,
                                                 rheader.status,
                                                 rheader.reason,
                                                 rcontent))

        LOG.debug("-- _push() ... stop ... --")

    def add(self, triple, context=None, quoted=False):
        """ Add a triple to the store.
            Apply the modifications on the cache, trigger an exception if data
            has already been modified on the server.
            
            :param triple: Triple (subject, predicate, object) to add.
            :param context: 
            :param quoted: The quoted argument is interpreted by formula-aware
                stores to indicate this statement is quoted/hypothetical. It
                should be an error to not specify a context and have the
                quoted argument be True. It should also be an error for the
                quoted argument to be True when the store is not
                formula-aware.

            :returns: 
        """

        LOG.debug("-- ProxyStore.add(triple=%s, context=%s, quoted=%s) --", 
                  triple, context, quoted)

        assert self._identifier is not None, "The store must be open."

        # TODO LATER : Wrong, assert is made to test bugs
        assert self._format is not None, "The store must be open."
        assert quoted == False, "The store -proxyStore- is not formula-aware"

        Store.add(self, triple, context, quoted)

        # Instruction suivant extraite du plugin Sleepycat
        # Store.add(self, (subject, predicate, object), context, quoted)
        self._graph.add(triple)


    def remove(self, triple, context):
        """Remove the set of triples matching the pattern from the store

        :param triple: Triple (subject, predicate, object) to remove.
        :param context: 

        :returns: 
        """
        # pylint: disable-msg=W0222
        # Signature differs from overriden method
        LOG.debug("-- ProxyStore.remove(triple=%s, context=%s) --", 
                  triple, context)

        Store.remove(self, triple, context)

        if triple == (None, None, None):
            self._graph = Graph()
            # the default implementation of Graph is not efficient in doing
            # this, so better create a new empty one
        else:
            self._graph.store.remove(triple)


    def triples(self, triple, context=None):
        """ Returns an iterator over all the triples (within the conjunctive
        graph or just the given context) matching the given pattern.

        :param triple: Triple (subject, predicate, object) to remove.
        :param context: ProxyStore is not context aware but it's internal
            cache IOMemory store is. Avoid context parameter.

        :returns: An iterator over the triples.
        """
        LOG.debug("-- ProxyStore.triples(triple=%s, context=%s) --", 
                  triple, context)

        Store.triples(self, triple) #, context=None)

        self._pull()

        return self._graph.store.triples(triple) #, context=None)

    def __len__(self, context=None):
        """ Number of statements in the store.

            :returns: The number of statements in the store.
        """
        self._pull()
        ret = len(self._graph)
        LOG.debug("******** __len__ : ProxyStore, nb statements %d", ret)
        return ret

    # ---------- Formula / Context Interfaces ---------- 
    #def contexts(self, triple=None):
    # Generator over all contexts in the graph. If triple is specified, a
    # generator over all contexts the triple is in.
    #def remove_context(self, identifier)
    # ---------- Formula / Context Interfaces ---------- 

    # ---------- Optional Transactional methods ---------- 
    def commit(self):
        """ Sends the modifications to the server.
        """
        self._push()

    def rollback(self):
        """ Cancel the modifications. Get the graph from the server.
        """
        self._pull()

    # ---------- Optional Transactional methods ---------- 

    def close(self, commit_pending_transaction=False):
        """ This closes the database connection. 

            :param commit_pending_transaction: Specifies whether to commit all
                pending transactions before closing (if the store is
                transactional). 
        """
        LOG.debug("******** close (%s) ", commit_pending_transaction)

        self._identifier = None
        self._etags = None
        self.configuration = None

        self._format = None
        self._graph.close()

        self.httpserver.clear_credentials()

    def destroy(self, configuration):
        """ This destroys the instance of the store identified by the
        configuration string.

        :param configuration: Configuration string identifying the store
        """
        LOG.debug("******** destroy (%s) ", configuration)

    def query(self, query, initNs=None, initBindings=None, queryGraph=None, 
              **kw): 
        """ I provide SPARQL query processing as a store.

        I simply pass through the query to the underlying graph. This prevents
        an external SPARQL engine to make multiple accesses to that store,
        which can generate HTTP traffic.
        """
        # initNs and initBindings are invalid names for pylint (C0103), but
        # method `query` is specified by rdflib, so #pylint: disable=C0103
        if initNs is None:
            initNs = {}
        if initBindings is None:
            initBindings = {}
        self._pull()
        return self._graph.query(query, initNs=initNs,
                                 initBindings=initBindings, **kw)

class GraphChangedError(Exception):
    """ Exception to be raised when the user tries to change graph data
        but the graph has already changed on the server.
    """
    def __init__(self, url=None, msg=None):
        self.url = url
        message = ("The graph has already changed on the server at %s,"
                   " the cache is not up to date. HTTP error %s") % (url, msg)
        Exception.__init__(self, message)

class ServerError(Exception):
    """ Exception to be raised when the server issues a 5xx error.
    """
    def __init__(self, url=None, msg=None):
        self.url = url
        message = "Server error at <%s>: %s" % (url, msg)
        Exception.__init__(self, message)

class StoreIdentifierError(Exception):
    """ Exception to be raised when the user tries to create a ProxyStore
        and to use it immediately with a wrong identifier. 
    """
    def __init__(self, identifier=None):
        message = ("The identifier is empty or invalid %s") % (identifier,)
        Exception.__init__(self, message)

class ResourceAccessError(Exception):
    """ Exception to be raised when the user tries to create a ProxyStore
        but the URI (identifier) is not valid or the configuration 
        (e.g credentials) is not valid.
    """
    def __init__(self, retcode=None, identifier=None, configuration=None):
        self.retcode = retcode
        self.identifier = identifier
        self.configuration = configuration
        message = "Got status %s on <%s> with config %r" % (retcode,
                                                            identifier,
                                                            configuration)
        Exception.__init__(self, message)
