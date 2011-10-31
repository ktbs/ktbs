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
#    GNU Lesser General Public License fo more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with KTBS.  If not, see <http://www.gnu.org/licenses/>.

"""
I contain useful namespace objects.
"""

from rdflib.namespace import Namespace, ClosedNamespace

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

KTBS = ClosedNamespace(
    "http://liris.cnrs.fr/silex/2009/ktbs#", [
        "AttributeType",
        "Base",
        "BuiltinMethod",
        "ComputedTrace",
        "KtbsRoot",
        "Method",
        "Obsel",
        "ObselType",
        "RelationType",
        "StoredTrace",
        "TraceModel",
        "contains",
        "external",
        "filter",
        "fusion",
        "hasAttributeDomain",
        "hasAttributeRange",
        "hasBase",
        "hasBegin",
        "hasBeginDT",
        "hasBuiltinMethod",
        "hasDefaultSubject",
        "hasEnd",
        "hasEndDT",
        "hasMethod",
        "hasModel",
        "hasObselCollection",
        "hasOrigin",
        "hasParameter",
        "hasParentMethod",
        "hasParentModel",
        "hasRelationDomain",
        "hasRelationRange",
        "hasSource",
        "hasSourceObsel",
        "hasSubject",
        "hasSuperObselType",
        "hasSuperRelationType",
        "hasTrace",
        "hasTraceBegin",
        "hasTraceBeginDT",
        "hasTraceEnd",
        "hasTraceEndDT",
        "hasUnit",
        "parallel",
        "sparql",
        ]
    )
