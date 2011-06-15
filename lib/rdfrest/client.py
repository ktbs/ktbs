# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Françoise Conil /
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
RDF-REST Client module.

I implement an rdflib store that acts as a proxy to a RESTful RDF graph.
"""

from rdflib.store import Store, VALID_STORE
  #, CORRUPTED_STORE, NO_STORE, UNKNOWN
from rdflib.graph import Graph
#from rdflib.term import URIRef

# TODO We should scan rdflib registered parsers : rdflib/plugin.py
#      rdflib has a turtle serializer but no turtle parser
#from rdflib.parser import Parser
#from rdflib.serializer import Serializer
#from rdflib.plugin import plugins

import httplib
import httplib2
from StringIO import StringIO
import os

#http://docs.python.org/howto/logging-cookbook.html
import logging
LOG = logging.getLogger(__name__)

_CONTENT_TYPE_PARSERS = {}
_CONTENT_TYPE_SERIALIZERS = {}

FORMAT_N3   = "n3"
FORMAT_XML  = "xml"
FORMAT_RDFA = "rdfa"
FORMAT_NT   = "nt"
FORMAT_TRIX = "trix"

def _get_rdflib_parsers():
    """ Try to get rdflib registered Parsers.
        TODO But how to make an automatic match Content-Type / rdflib parser ?
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

    _CONTENT_TYPE_PARSERS["application/rdf+xml"] = "application/rdf+xml"

def _get_rdflib_serializers():
    """ Try to get rdflib registered Serializers.
        TODO Automate ?
    """
    _CONTENT_TYPE_SERIALIZERS[FORMAT_N3] = "text/turtle"
    _CONTENT_TYPE_SERIALIZERS[FORMAT_XML] = "application/rdf+xml"

# Build rdflib parsers list from content-type
_get_rdflib_parsers()

# Build rdflib serializers list 
_get_rdflib_serializers()

class ProxyStore(Store):
    """
    A Proxy store implemention.
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

            :param configuration: Configuration string of the store
            :param identifier: URIRef identifying the store
        """

        # Use the defaut for internal graph storage, IOMemory
        # We should specify the default internal storage explicitely.
        Store.__init__(self)
        self._identifier = identifier
        self.configuration = configuration

        self._format = None
        self._graph = Graph()

        self._etags = None

        # Show the network activity
        #httplib2.debuglevel = 1

        # TODO !!! Replace by a configurable path for HTTPLIB2 cache
        # As it is a file cache, it is conserved between two executions
        # Should we delete the directory on application end (i.e close()) ?
        self.httpserver = httplib2.Http(os.getcwd() + "/.cache")

    def _parse_header(self, header):
        """ Parses the header of the HTTP request or response.
        """
        # TODO Arbitrary default value to be decided
        self._format = FORMAT_N3

        # Extract Content-Type
        content_type = header['content-type']
        if len(content_type) > 0:
            content_type = content_type.split(";", 1)[0].strip()
            # Format contains corresponding rdflib format
            self._format = _CONTENT_TYPE_PARSERS[content_type]
            #print "Content-Type %s, rdflib parser %s" % (content_type,
            #                                             self._format)

        self._etags = header.get('etag')

    def _parse(self, header, content):
        """ Parses the received data to build the graph to cache.
            TODO Analyse Content-Type HTTP header to determine
                 the serialization used
            TODO The serialization must be stored
        """
        self._parse_header(header)

        # Creates the graph
        self._graph.parse(StringIO(content), format=self._format)

    def _push(self):
        """ Send data to server.
            Apply the modifications on the cache, trigger an exception if data
            has already been modified on the server.
        """

        LOG.debug("************************ beginning _push () "
                      "************************************")

        # TODO : How to build the "PUT" request ?
        # Which data in the header ? 
        # Which serialization ? The same as we received but does rdflib supply
        # all kind of parsing / serialization ?
        headers = {'Content-Type': '%s; charset=UTF-8'
                   % _CONTENT_TYPE_SERIALIZERS[self._format],}
        if self._etags:
                   headers['If-Match'] = self._etags
        data = self._graph.serialize(format=self._format)

        LOG.debug("[sent headers]\n%s", headers)
        LOG.debug("[sent data]\n%s", data)

        # TODO : Analyze the server response
        #        The server will tell if the graph has changed
        #        The server will supply new ETags ... update the data with the
        # response
        rheader, rcontent = self.httpserver.request(self.configuration,
                                                    'PUT',
                                                    data,
                                                    headers=headers)

        LOG.debug("[response header]\n%s", rheader)
        LOG.debug("[response content]\n%s", rcontent)

        if rheader.status in (httplib.OK,):
            self._parse_header(rheader)
        else:
            raise GraphChangedError(url=self.configuration, msg=rheader.status)

        LOG.debug("************************ ending _push () "
                      "***************************************")

    def _pull(self):
        """Update cache before an operation.
           This method must be called before each get-type request.
        """
        LOG.debug("************************ beginning _pull () "
                      "************************************")

        header, content = self.httpserver.request(self.configuration)

        LOG.debug("[received header]\n%s", header)
        LOG.debug("[received content]\n%s", content)

        # TODO Define use-cases
        # We should check ETags too ?
        if not header.fromcache or self._format is None:
            if self._format is None:
                LOG.debug("Creating proxy graph  ....")
            else:
                LOG.debug("Updating proxy graph  ....")

            self._parse(header, content)
            
        else:
            LOG.debug("Proxy graph is up to date ...")

        LOG.debug("************************ ending _pull () "
                      "***************************************")

    def open(self, configuration, create=False):
        """ Opens the store specified by the configuration string. 
            An exception is also raised if a store exists, but there is
            insufficient permissions to open the store.

            :param configuration: Configuration string of the store
            :param create: If create is True a store will be created if it does
            not already exist. If create is False and a store does not already
            exist an exception is raised. 

            :returns: VALID_STORE on success
                      NO_STORE
        """
        LOG.debug("#################  Creating ProxyStore for %s "
                      "##############", configuration)

        # TODO En cas de create=True inutile de récupérer quoique ce soit
        self.configuration = configuration

        self._pull()

        return VALID_STORE

    def add(self, triple, context=None, quoted=False):
        """ Add a triple to the store.
            Apply the modifications on the cache, trigger an exception if data
            has already been modified on the server.
            
            :param triple: Triple (subject, predicate, object) to add.
            :param context: 
            :param quoted: The quoted argument is interpreted by formula-aware
            stores to indicate this statement is quoted/hypothetical. It should
            be an error to not specify a context and have the quoted argument
            be True. It should also be an error for the quoted argument to be
            True when the store is not formula-aware. 

            :returns: 
        """

        LOG.debug("******** add (%s, %s, %s) ", triple, context, quoted)

        assert self._format is not None, "The store must be open."
        assert quoted == False, "The store -proxyStore- is not formula-aware"

        # Instruction suivant extraite du plugin Sleepycat
        # Store.add(self, (subject, predicate, object), context, quoted)
        self._graph.add(triple)

        self._push()

    def remove(self, triple, context):
        """ Remove the set of triples matching the pattern from the store

            :param triple: Triple (subject, predicate, object) to remove.
            :param context: 

            :returns: 
        """
        # pylint: disable-msg=W0222
        # Signature differs from overriden method
        LOG.debug("******** remove (%s, %s) ", triple, context)

        self._graph.store.remove(triple)
        self._push()

    def triples(self, triple, context=None):
        """ Returns an iterator over all the triples (within the conjunctive
        graph or just the given context) matching the given pattern.

            :param triple: Triple (subject, predicate, object) to remove.
            :param context: 

            :returns: An iterator over the triples.
        """
        LOG.debug("******** triples (%s, %s) ", triple, context)

        self._pull()

        #for (s, p, o), cg in self._graph.store.triples(triple, context):
        #    yield (s, p, o)

        return self._graph.store.triples(triple, context)

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
    #def commit(self):
    #def rollback(self):
    # ---------- Optional Transactional methods ---------- 

    def close(self, commit_pending_transaction=False):
        """ This closes the database connection. 
            :param commit_pending_transaction: Specifies whether to commit all
            pending transactions before closing (if the store is
            transactional). 
        """
        LOG.debug("******** close (%s) ", commit_pending_transaction)

        self._identifier = None
        self.configuration = None

        self._format = None
        self._graph.close()

        self._etags = None

    def destroy(self, configuration):
        """ This destroys the instance of the store identified by the
        configuration string.

            :param configuration: Configuration string identifying the store
        """
        LOG.debug("******** destroy (%s) ", configuration)

class GraphChangedError(Exception):
    """ Exception to be raised when the user tries to change graph data
        but the graph has already changed on the server.
    """
    def __init__(self, url=None, msg=None):
        self.url = url
        message = ("The graph has already changed on the server at %s,"
                   " the cache is not up to date. HTTP error %s") % (url, msg)
        Exception.__init__(self, message)
