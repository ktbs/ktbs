#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
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
ProxyStore test program. 
Use nose, http://somethingaboutorange.com/mrl/projects/nose/1.0.0/testing.html
TODO use setup and teardown methods for test fixture teardown could remove 
the http cache.
"""

from rdflib import Namespace, BNode, Literal, URIRef
from rdflib.graph import Graph
from rdflib.store import VALID_STORE, CORRUPTED_STORE, NO_STORE, UNKNOWN

from nose.tools import raises
from os.path import abspath, dirname, join
from subprocess import Popen, PIPE
from time import sleep
from unittest import skip

from rdfrest.proxystore import ProxyStore
from rdfrest.proxystore import StoreIdentifierError, GraphChangedError
from rdfrest.proxystore import PS_CONFIG_URI, PS_CONFIG_USER, PS_CONFIG_PWD
from rdfrest.proxystore import PS_CONFIG_HTTP_CACHE, PS_CONFIG_HTTP_RESPONSE

import logging

from .example1 import make_example1_httpd

THREAD = None
HTTPD = None

def setUp():
    global THREAD, HTTPD
    THREAD, HTTPD = make_example1_httpd()
    # disabling logging
    HTTPD.RequestHandlerClass.log_message = (lambda *args: None)

def tearDown():
    global THREAD, HTTPD
    if HTTPD is not None:
        HTTPD.shutdown()
    if THREAD is not None:
        THREAD.join()
    THREAD, HTTPD = None, None
    

def test_identifier_no_open():
    """ Pass the URI as identifier to __init__() but does not explicitely
        call open(). Should be OK.
    """
    store = ProxyStore(identifier="http://localhost:1234/foo")
    graph = Graph(store=store)
    gs = graph.serialize()
    #print gs
    graph.close()

def test_identifier_no_configuration():
    """ Pass the URI as identifier to __init__() then call open() with no
        configuration parameter.
    """

    store = ProxyStore(identifier="http://localhost:1234/foo")
    graph = Graph(store=store)
    graph.open({})
    gs = graph.serialize()
    #print gs
    graph.close()

def test_no_identifier_uri_in_open():
    """ Nothing passed to __init__(), uri passed to explicit open().
        Should be OK.
    """

    store = ProxyStore()
    graph = Graph(store=store)
    graph.open({PS_CONFIG_URI: "http://localhost:1234/foo"})
    gs = graph.serialize()
    #print gs
    graph.close()

@skip("credentials not supported by example1.py")
def test_uri_with_good_credentials_in_init():
    """ Pass an URI to __init__() and good credentials in configuration.
        Should be OK.
    """

    store = ProxyStore(configuration={PS_CONFIG_USER: "user",
                                      PS_CONFIG_PWD: "pwd"},
                       identifier="http://localhost:1234/foo")
    graph = Graph(store=store)
    graph.close()

@skip("credentials not supported by example1.py")
def test_uri_with_wrong_credentials_in_init():
    """ Pass an URI to __init__() and wrong credentials in configuration.
    """

    store = ProxyStore(configuration={PS_CONFIG_USER: "user",
                                      PS_CONFIG_PWD: "wrong-pwd"},
                       identifier="http://localhost:1234/foo")
    graph = Graph(store=store)
    graph.close()

@skip("credentials not supported by example1.py")
def test_uri_with_good_credentials_in_open():
    """ Pass an URI to __init__() and good credentials in configuration.
        Should be OK.
    """

    store = ProxyStore(identifier="http://localhost:1234/foo")
    graph = Graph(store=store)
    graph.open(configuration={PS_CONFIG_USER: "user",
                              PS_CONFIG_PWD: "pwd"})
    graph.close()

@raises(StoreIdentifierError)
def test_no_uri():
    """ Pass no URI to __init__() nor to open().
    """

    store = ProxyStore()
    graph = Graph(store=store)
    graph.open({})
    graph.close()

@raises(StoreIdentifierError)
def test_different_uris():
    """ Pass different URIs to __init__() and to open().
    """

    store = ProxyStore(identifier="http://localhost:1234/foo")
    graph = Graph(store=store)
    graph.open({PS_CONFIG_URI: "http://localhost:1234/foo/group1/"})
    graph.close()

@raises(AssertionError)
def test_no_uri_no_open():
    """ Nothing passed to __init__(), and open() is not called either.
        Try to manipulate the graph, should trigger an error.
    """

    store = ProxyStore()
    graph = Graph(store=store)
    gs = graph.serialize()
    graph.close()

if __name__ == '__main__':
    """ Useful if I want the ProxyStore logs."""
    test_identifier_no_open()
    test_identifier_no_configuration()
    test_no_identifier_uri_in_open()
    test_no_uri()
    test_different_uris()
    test_no_uri_no_open()
