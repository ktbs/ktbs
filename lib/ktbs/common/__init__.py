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
* __eq__ and __hash__ methods
* a property uri: a URIRef identifying this resource
* a method ``make_resource(node, context=None)`` used to build another resource
  as the value of a property.

Note that not all classes in `ktbs.server` inherit the corresponding mixin
class from `ktbs.common`, and when they do, they sometimes use low-level code
when the mixin class provides a high-level interface, mostly for performance
considerations.
"""
