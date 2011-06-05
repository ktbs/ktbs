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
import subprocess # see at the end of file why we don't "impot from"

from ...serializer import serializer_profile

@serializer_profile("text/plain", "dot", 10) 
def generate_dot(namespaces, graph, uri):
    """
    I serialize graph in the graphviz format.
    """
    # TODO MAJOR implement dot serializer
    #pylint: disable=W0613
    #   parameters not used (remove this once implemented)
    raise NotImplementedError("dot serialization temporarily unavailable")

@serializer_profile("image/png", "png", 10) 
def generate_png(namespaces, graph, uri):
    """
    I serialize graph in PNG.
    """
    return _generate_format("png", namespaces, graph, uri)

@serializer_profile("image/svg+xml", "svg", 10) 
def generate_svg(namespaces, graph, uri):
    """
    I serialize graph in SVG.
    """
    return _generate_format("svg", namespaces, graph, uri)

def _generate_format(format_, namespaces, graph, uri):
    """
    I serialize graph to the given format using graphviz.
    """
    dot_str = generate_dot(namespaces, graph, uri)
    dot2format = _POPEN(["dot", "-T%s" % format_], stdin=_PIPE, stdout=_PIPE)
    out, _ = dot2format.communicate(dot_str)
    status = dot2format.wait()
    if status != 0:
        raise Exception("Serializer Error (process 'dot' failed)")
    return out

# for some reaon, pylint errs when we import the following symbols with::
#     from subprocess import PIPE, Popen
# so we fallback to the following hack
_POPEN = subprocess.Popen
_PIPE = subprocess.PIPE
