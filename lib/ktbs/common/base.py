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
I provide the pythonic interface to bases.
"""
from ktbs.common.utils import extend_api
from ktbs.namespaces import KTBS

from rdflib import RDFS

@extend_api
class BaseMixin(object):
    """
    I provide the pythonic interface common to bases.
    """

    def get_label(self):
        """
        I return a rdfs:label, if any, of this base.
        """
        return next(self.graph.objects(self.uri, _LABEL), None)

    def iter_labels(self):
        """
        I iter over all rdfs:label of this base.
        """
        make_resource = self.make_resource
        for label in self.graph.objects(self.uri, _LABEL):
            yield make_resource(label)

    def iter_contained(self):
        """
        I iter over all elements contained by this base.
        """
        make_resource = self.make_resource
        for elt in self.graph.objects(self.uri, _CONTAINS):
            yield make_resource(elt)

    # TODO MAJOT implement iter_traces, iter_models, iter_methods

        
_CONTAINS = KTBS.contains    
_LABEL = RDFS.label
