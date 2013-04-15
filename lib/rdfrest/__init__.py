# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
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

"""RDF-REST is a framework for building applications that

* expose their functionalities in a RESTful way, and/or
* use RESTful services.

For a high-level descripription, refer to [Champin2013]_.

RDF-REST provides a python abstraction of REST resources,
so that client code can handle and mix local and remote resources
in a completely transparent way.

In a nutshell, a RESTful application is made of a set of *resources*, which:

* are identified by a URI,
* expose a uniform interface,
* have an internal state that can be serialized in one or different formats,
* link to each other.

More precisely, in RDF-REST:

* the uniform interface of resources is defined by :class:`.cores.ICore`;
* RDF is used as a unifying model to represent resource's states (with the
  RDFLib_ library);
* :mod:`.serializers` and :mod:`.parsers` provide an extensible framework for
  supporting multiple formats.

.. _RDFLib: http://rdflib.readthedocs.org/en/latest/
"""

import rdflib
assert rdflib.__version__[0] == "4"

import rdfrest.util.compat
