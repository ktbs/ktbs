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
I provide the pythonic interface common to all kTBS resources.
"""
from rdflib import Literal, RDFS

from ktbs.namespaces import SKOS
from ktbs.common.utils import extend_api, short_name

@extend_api
class ResourceMixin(object):
    """
    I provide the pythonic interface common to all kTBS resources.
    """

    # NB: do not implement get_uri and get_graph, as @extend_api may override
    # the underlying attributes uri and graph

    def get_label(self):
        """
        Return a user-friendly label for this resource.
        """
        # TODO MINOR use transaction with graph
        pref_label = next(self.graph.objects(self.uri, SKOS.prefLabel), None)
        if pref_label is not None:
            return pref_label
        label = next(self.graph.objects(self.uri, RDFS.label), None)
        if label is not None:
            return label
        return short_name(self.uri)

    def set_label(self, value):
        """
        Set the skos:prefLabel of this resource.
        """
        # TODO MINOR use transaction with graph
        self.del_label()
        self.graph.add((self.uri, SKOS.prefLabel, Literal(value)))

    def del_label(self):
        """
        Remove the skos:prefLabel of this resource.
        """
        self.graph.remove((self.uri, SKOS.prefLabel, None))
