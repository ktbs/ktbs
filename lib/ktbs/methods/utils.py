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
Utility functions for method implementations.
"""
from rdflib import URIRef

def translate_node(node, transformed_trace, src_uri, multiple_sources):
    """
    If node is a URI, translate its URI to put it in transfored_trace. Else,
    leave it unchanged.
    """
    if not isinstance(node, URIRef):
        return node
    if not node.startswith(src_uri):
        return node
    if multiple_sources:
        _, tid, oid = node.rsplit("/", 2)
        new_id = "%s_%s" % (tid, oid)
    else:
        _, new_id = node.rsplit("/", 1)
    return URIRef("%s%s" % (transformed_trace.uri, new_id))

