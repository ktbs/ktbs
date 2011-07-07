#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/silex/2009/ktbs>
#    Copyright (C) 2011 Françoise Conil <fconil@liris.cnrs.fr> / SILEX
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

from rdfrest.client import ProxyStore
from rdfrest.client import StoreIdentifierError, GraphChangedError
from rdfrest.client import PS_CONFIG_URI, PS_CONFIG_USER, PS_CONFIG_PWD
from rdfrest.client import PS_CONFIG_HTTP_CACHE, PS_CONFIG_HTTP_RESPONSE

import logging

PROCESS = None

def setUp():
    global PROCESS
    PROCESS = Popen([join(dirname(dirname(abspath(__file__))),
                          "test", "rdfrest_demo.py")], stderr=PIPE)
    # then wait for the server to actually start:
    # we know that it will write on its stderr when ready
    PROCESS.stderr.read(1)

def tearDown():
    PROCESS.terminate()
    

def test_identifier_no_open():
    """ Pass the URI as identifier to __init__() but does not explicitely
        call open(). Should be OK.
    """
    store = ProxyStore(identifier="http://localhost:8001/")
    graph = Graph(store=store)
    gs = graph.serialize()
    #print gs
    graph.close()

def test_identifier_no_configuration():
    """ Pass the URI as identifier to __init__() then call open() with no
        configuration parameter.
    """

    store = ProxyStore(identifier="http://localhost:8001/")
    graph = Graph(store=store)
    graph.open({})
    graph.close()

def test_no_identifier_uri_in_open():
    """ Nothing passed to __init__(), uri passed to explicit open().
        Should be OK.
    """

    store = ProxyStore()
    graph = Graph(store=store)
    graph.open({PS_CONFIG_URI: "http://localhost:8001/"})
    graph.close()

def test_uri_with_good_credentials_in_init():
    """ Pass an URI to __init__() and good credentials in configuration.
        Should be OK.
    """

    store = ProxyStore(configuration={PS_CONFIG_USER: "user",
                                      PS_CONFIG_PWD: "pwd"},
                       identifier="http://localhost:8001/")
    graph = Graph(store=store)
    graph.close()

def test_uri_with_wrong_credentials_in_init():
    """ Pass an URI to __init__() and wrong credentials in configuration.
    """

    store = ProxyStore(configuration={PS_CONFIG_USER: "user",
                                      PS_CONFIG_PWD: "wrong-pwd"},
                       identifier="http://localhost:8001/")
    graph = Graph(store=store)
    graph.close()

def test_uri_with_good_credentials_in_open():
    """ Pass an URI to __init__() and good credentials in configuration.
        Should be OK.
    """

    store = ProxyStore(identifier="http://localhost:8001/")
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

    store = ProxyStore(identifier="http://localhost:8001/")
    graph = Graph(store=store)
    graph.open({PS_CONFIG_URI: "http://localhost:8001/another_uri/"})
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
