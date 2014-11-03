# -*- coding: utf-8 -*-
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
A plugin to allow POSTing obsels to a StoredTrace with a GET.

This is of course a Bad Thing™, as GET requests should be safe and idempotent.
However, this is required in some contexts
where issuing a POST request is not possible.

The protocol is to GET (trace_uri)?ctype=(content-type)&post=(payload)

"""
from rdflib import Graph
from rdfrest.exceptions import ParseError
from rdfrest.parsers import get_parser_by_content_type

from ktbs.engine.trace import StoredTrace as OriginalStoredTrace

class StoredTrace(OriginalStoredTrace):

    def get_state(self, parameters=None):
        """I implement :meth:`.interface.ICore.get_state`.

        If parameters contains 'ctype' and 'post', I perform a post instead.
        """
        if parameters is not None and "post" in parameters:
            ctype = parameters.get("ctype", "text/json")
            parser, _ = get_parser_by_content_type(ctype)
            if parser is None:
                raise ParseError("unknown content-type %s" % ctype)
            graph = parser(parameters["post"], self.uri, "utf-8")
            self.post_graph(graph, None)
            return Graph()
        else:
            return super(StoredTrace, self).get_state(parameters)


def start_plugin(_config):
    # replace original StoredTrace by our patched version
    import ktbs.engine.service
    ktbs.engine.service.StoredTrace = StoredTrace
