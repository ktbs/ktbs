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
KTBS: Kernel for Trace-Based Systems.

.. _ktbs-resource-creation:

Resource creation
=================

Most methods for creating a KTBS resource have the same final parameters `id`
and `graph`.

`id` is specified in the :ref:`abstract-ktbs-api`: it is optional but can be
used to set the URI of the resource to create (else, the KTBS will generate a
URI). If provided, it must of course be an acceptable URI (not already in use,
and subordinated to the parent's URI). As specified by the
:ref:`abstract-ktbs-api`, `id` can be provided as character string,
representing a URI either absolute or relative to the parent's URI. The Python
implementation also accepts a `rdflib.URIRef`:class: or any object with a
`uri` attribute returning a `~rdflib.URIRef`:class:.

`graph` is an additional parameter where the user can specify arbitrary
properties for the resource to create. This assumes that the resource can be
identified in the graph, which is trivial is `id` is provided. However, if the
user wants to provide a `graph` but also wants to let the KTBS mint a URI for
the created resource, they can use a blank node (:class:`rdflib.BNode`) to
represent the resource in `graph`, and pass it to `id`.
"""

