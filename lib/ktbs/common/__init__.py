#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
I provide pythonic interfaces for KTBS elements as mixin classes, to be reused
in server, client and script.

All those mixin require

* a property `uri`: a `~rdflib.URIRef`:class: identifying this resource

* a property `_graph`: a `~rdflib.Graph`:class: containing a readt
  description of this resource, that will only be used for reading

* a property `_edit`: a python-context returning a mutable
  `~rdflib.Graph`:class: and commiting the modifications to the
  resource on exit

* a method `make_resource(node, node_type=None, graph=None)` used to build
  another resource as the value of a property. node_type (a URI) and graph
  can be provided as a hint to accelerate the process.

Note that not all classes in `ktbs.local` inherit the corresponding mixin
class from `ktbs.common`, and when they do, they sometimes use low-level code
when the mixin class provides a high-level interface, mostly for performance
considerations.
"""
