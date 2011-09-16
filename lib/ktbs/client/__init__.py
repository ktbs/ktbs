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
I provide a python implementation of the abstract client API for kTBS.

I implement the following adaptations to the abstract client API:

* adaptations suggested by the abstract client API:

  * read-only or read-write properties corresponding to get/set methods
  * read-only properties corresponding to list methods
  * iter methods corresponding to list methods

* specific adaptation:

  * Anytime an object with a ``uri`` property is expected, passing a URI should
    also work (including a URI relative to the target object).
    For example, the 'model' agrgument of Base.create_stored_trace can be a URI
    (as a unicode or an rdflib.URIRef) rather than an instance of Model.

  * Datetimes can be used instead of integers for representing timecodes in
    traces when the trace model and origin allow the conversion.
"""
