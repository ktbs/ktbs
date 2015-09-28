#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
I provide the common implementation of all local KTBS resources.
"""
from rdflib import Namespace, URIRef
from re import compile as RegExp, UNICODE

from rdfrest.cores.local import EditableCore
from rdfrest.cores.mixins import BookkeepingMixin, FolderishMixin, \
    GraphPostableMixin, WithCardinalityMixin, WithReservedNamespacesMixin, \
    WithTypedPropertiesMixin
from ..api.resource import KtbsResourceMixin
from ..namespace import KTBS
from ..utils import mint_uri_from_label, SKOS


METADATA = Namespace("tag:silex.liris.cnrs.fr.2012.08.06.ktbs.metadata:")


class KtbsResource(KtbsResourceMixin, WithCardinalityMixin,
                   WithReservedNamespacesMixin, WithTypedPropertiesMixin,
                   BookkeepingMixin, EditableCore):
    """I provide common methods and class parameters for all KTBS Resources.

    Especially, I include a number of of required other mixins.
    """
    ######## ILocalCore (and mixins) implementation  ########

    RDF_RESERVED_NS = [KTBS]

    @classmethod
    def mint_uri(cls, target, new_graph, created, basename=None, suffix=""):
        """I override :meth:`rdfrest.cores.local.ILocalCore.mint_uri`.

        I use the skos:prefLabel of the resource to mint a URI, else the
        basename (if provided), else the class name.
        """
        label = (new_graph.value(created, SKOS.prefLabel)
                 or basename
                 or cls.__name__)
        return mint_uri_from_label(label, target, suffix=suffix)


class KtbsPostableMixin(FolderishMixin, GraphPostableMixin, KtbsResource):
    """I implement the common post-related functionalities for KtbsResources.
    """

    def check_posted_graph(self, parameters, created, new_graph):
        """I implement
        :meth:`rdfrest.cores.local.GraphPostableMixin.check_posted_graph`.
        """
        diag = super(KtbsPostableMixin, self) \
            .check_posted_graph(parameters, created, new_graph)
        if isinstance(created, URIRef):
            if not created.startswith(self.uri):
                diag.append("The URI of the created item is not consistent "
                            "with the URI of its container: <%s>" % created)
            else:
                ident = created[len(self.uri):]
                if ident[-1] == "/":
                    ident = ident[:-1]
                if not _VALID_IDENT_RE.match(ident):
                    diag.append("The identifier of the created item is "
                                "invalid: [%s]" % ident)
        return diag

_VALID_IDENT_RE = RegExp("[\w\-]+\Z", UNICODE)

