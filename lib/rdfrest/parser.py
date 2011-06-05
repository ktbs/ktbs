#    This file is part of RDF-REST <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
TODO docstring
"""
from rdflib import Graph

# TODO should implement a mechanism similar to serializer.py

def parse(filelike, mimetype, base=None):
    """
    Parse the content of `filelike` according to `mimetype` into an RDF graph.
    """
    ret = Graph()
    ret.parse(filelike, format = _MIME2RDFLIB.get(mimetype, "default"),
              publicID=base)
    return ret
    
_MIME2RDFLIB = {
    "application/rdf+xml": "xml",
    "text/turtle": "n3",
    "text/turtle;charset=utf-8": "n3",
    "text/x-turtle": "n3",
    "application/turtle": "n3",
    "application/x-turtle": "n3",
    "text/n3": "n3",
    "text/n3;charset=utf-8": "n3",
    "text/plain": "nt",
    "text/html": "rdfa",
    "application/xhtml+xml": "rdfa",
    "application/trix": "trix",
    "application/trix+xml": "trix",
}
