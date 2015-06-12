#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Runs kTBS behind a WSGI-enabled HTTP server.

This file MUST be accompanied, in the same directory,
by a file with the same name plus the ".conf" extension.

All configuration happens in the .conf file,
you should normally not have to modify this file (the .wsgi file).
"""

####
import atexit

from ktbs.engine.service import get_ktbs_configuration, KtbsService
from rdfrest.util.config import apply_global_config
from rdfrest.http_server import SparqlHttpFrontend


ktbs_config_path = __file__ + ".conf"
ktbs_config = get_ktbs_configuration(open(ktbs_config_path))
apply_global_config(ktbs_config)

ktbs_service = KtbsService(ktbs_config)
atexit.register(lambda: ktbs_service.store.close())

#application = HttpFrontend(ktbs_service, ktbs_config)
# or, if you want SPARQL support:
application = SparqlHttpFrontend(ktbs_service, ktbs_config)

