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
from ktbs.common.utils import extend_api_ignore, extend_api, short_name

@extend_api
class ResourceMixin(object):
    """
    I provide the pythonic interface common to all kTBS resources.
    """

    @extend_api_ignore
    def get_uri(self):
        """
        Return the URI of this resource.
        """
        return self.uri
        # the decorator extend_api_ignore above prevents extend_api to create
        # a recursive loop by making a 'uri' prop using this method...

    def get_label(self):
        """
        Return a user-friendly label for this resource.
        """
        pref_label = self._graph.value(self.uri, SKOS.prefLabel)
        if pref_label is not None:
            return str(pref_label)

        label = self._graph.value(self.uri, RDFS.label)
        if label is not None:
            return str(label)

        ret = short_name(self.uri)
        if ret[-1] == "/":
            ret = ret[:-1]
        return ret

    def set_label(self, value):
        """
        Set the skos:prefLabel of this resource.
        """
        with self._edit as graph:
            graph.set((self.uri, SKOS.prefLabel, Literal(value)))

    def reset_label(self, value):
        """
        Reset the skos:prefLabel of this resource.
        """
        raise NotImplementedError()

    def del_label(self):
        """
        Remove the skos:prefLabel of this resource.
        """
        with self._edit as graph:
            graph.remove((self.uri, SKOS.prefLabel, None))
