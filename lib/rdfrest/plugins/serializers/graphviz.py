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
I provide a PNG serializer based on graphviz.
"""
from subprocess import PIPE, Popen

from rdfrest.exceptions import SerializeError
from rdfrest.serializer import register

@register("text/plain", "dot", 10) 
def serialize_dot(graph, _service, sregister, base_uri=None):
    """
    I serialize graph in the graphviz format.
    """
    # TODO MAJOR implement dot serializer
    #pylint: disable=W0613
    #   parameters not used (remove this once implemented)
    raise NotImplementedError("dot serialization temporarily unavailable")

@register("image/png", "png", 10) 
def serialize_png(graph, _service, sregister, base_uri=None):
    """
    I serialize graph in PNG.
    """
    return _serialize_format("png", graph, sregister, base_uri)

@register("image/svg+xml", "svg", 10) 
def serialize_svg(graph, _service, sregister, base_uri=None):
    """
    I serialize graph in SVG.
    """
    return _serialize_format("svg", graph, sregister, base_uri)

def _serialize_format(format_, graph, _service, sregister, base_uri=None):
    """
    I serialize graph to the given format using graphviz.
    """
    dot_str = "".join(serialize_dot(graph, sregister, base_uri))
    dot2format = Popen(["dot", "-T%s" % format_], stdin=PIPE, stdout=PIPE)
    out, _ = dot2format.communicate(dot_str)
    status = dot2format.wait()
    if status != 0:
        raise SerializeError("process 'dot' failed")
    return out
