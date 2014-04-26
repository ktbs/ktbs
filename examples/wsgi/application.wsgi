#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Runs kTBS behind a WSGI-enabled HTTP server.
"""

#### CHANGE THE VALUES BELOW ACCORDINGLY TO YOUR CONFIGURATION

RDF_STORE = "/var/dir/ktbs.db"                # where RDF data will be stored
ROOT_URI  = "https://example.com:1234/ktbs/"  # URI of the kTBS root
OPTIONS = {  # see rdfrest.http_server.HttpFrontend for available options
  #"cache_control": "no-cache",
  #"cors_allow_origin": "*",
  #"max_bytes": 1000000,
  #"max_triples": 1000,
}

####
import atexit
from os.path import join

from rdflib import URIRef

from ktbs.engine.service import make_ktbs
from ktbs.namespace import KTBS
from rdfrest.http_server import HttpFrontend, SparqlHttpFrontend
from rdfrest.serializers import bind_prefix, get_prefix_bindings

prefix_bindings = get_prefix_bindings()
for prefix in ["", "k", "ktbs", "ktbsns"]:
    if prefix not in prefix_bindings:
        bind_prefix(prefix, KTBS)
        break

ktbs_service = make_ktbs(URIRef(ROOT_URI), RDF_STORE).service
atexit.register(lambda: ktbs_service.store.close())
application = SparqlHttpFrontend(ktbs_service, **OPTIONS)
# or, if you don't want SPARQL support:
# application = HttpFrontend(ktbs_service, **OPTIONS)

