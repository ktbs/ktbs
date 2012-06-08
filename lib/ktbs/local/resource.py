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
I provide the common implementation of all local KTBS resources.
"""
from rdflib import RDF, URIRef
from rdfrest.resource import Resource as RdfRestResource
from rdfrest.mixins import RdfPostMixin, BookkeepingMixin, \
    WithReservedNamespacesMixin, WithCardinalityMixin
from rdfrest.utils import parent_uri, replace_node

from ktbs.common.utils import mint_uri_from_label
from ktbs.namespaces import KTBS, SKOS

class KtbsResourceMixin(WithCardinalityMixin, WithReservedNamespacesMixin,
                        RdfRestResource):
    """I provide common methods and class parameters for all KTBS Resources.

    Especially, I include a number of of required other mixins.
    """

    RDF_RESERVED_NS = [KTBS]

    def factory(self, uri, node_type=None, graph=None):
        """I make a resource with the given URI.

        NB: the service does not use the `node_type` and `graph` hints.
        """
        # unused argument 'graph' #pylint: disable=W0613
        ret = self.service.get(uri)
        assert ret.RDF_MAIN_TYPE == node_type
        return ret

    @classmethod
    def mint_uri(cls, target, new_graph, created, suffix=""):
        """I override :meth:`rdfrest.resource.Resource.mint_uri`.

        I use the skos:prefLabel of the resource to mint a URI, else the class
        name.
        """
        label = new_graph.value(created, SKOS.prefLabel) \
            or cls.__name__.lower()
        return mint_uri_from_label(label, target, suffix=suffix)


class KtbsPostMixin(BookkeepingMixin, RdfPostMixin, KtbsResourceMixin):
    """I provide support for POST to KtbsResourceMixin.
    """

    def ack_new_child(self, child_uri, child_type):
        """**Hook**: called after the creation of a new child resource.

        :param child_uri: the URI of the newly created child resource
        :param child_type: the type URI of the newly created child resource
        """
        pass

    KTBS_CHILDREN_TYPES = []

    def rdf_post(self, graph, parameters=None):
        created = super(KtbsPostMixin, self).rdf_post(graph, parameters)
        with self._edit:
            for i in created:
                itype = graph.value(i, RDF.type)
                self.ack_new_child(i, itype)
        return created

    def check_posted_graph(self, created, new_graph):
        """I override `rdfrest.mixins.RdfPostMixin.check_posted_graph`.

        If the class provides a ``KTBS_CHILDREN_TYPES`` attribute as a list
        of URIRef, I check that the posted resource is of one of these types.
        Note that, unlike other class constants used in
        :module:`rdfrest.mixins`, overriding KTBS_CHILDREN_TYPES does not
        magically inherit the values from the parent class.
        """
        diag = super(KtbsPostMixin, self)\
            .check_posted_graph(created, new_graph)

        allowed_types = getattr(self, "KTBS_CHILDREN_TYPES", None)
        if allowed_types:
            for rdf_type in new_graph.objects(created, RDF.type):
                if rdf_type in allowed_types:
                    break
            else:
                print "===", allowed_types
                diag.append("Posted resource not supported by %s" \
                                  % self.RDF_MAIN_TYPE)

        if isinstance(created, URIRef):
            parent = parent_uri(created)
            if parent != str(self.uri):
                diag.append("Posted resource's URI %s not child of target" \
                                  % created)

        return diag

    def _post_or_trust(self, py_class, node, graph, trust_graph):
        """Depending on the parameters, I use rdf_post or I efficiently
        create a resource with `py_class`.

        Note that I nevertheless do ``assert``'s to check the validity of the
        graph, so the efficiency gain may happen only in optimize model.
        """
        if isinstance(node, URIRef):
            # we need to call check_posted_graph, at least for checking the
            # validity of provided 'node'
            diag = self.check_posted_graph(node, graph)
            if not diag:
                raise ValueError(diag)
            uri = node
        else:
            uri = None

        if trust_graph:
            if uri is None:
                uri = py_class.mint_uri(self, graph, node)
                replace_node(graph, node, uri)
                assert self.check_posted_graph(uri, graph), \
                       self.check_posted_graph(uri, graph)

            assert py_class.check_new_graph(self.service, uri, graph), \
                   py_class.check_new_graph(self.service, uri, graph)
            with self.service:
                py_class.store_graph(self.service, uri, graph)
                self.ack_new_child(uri, py_class.RDF_MAIN_TYPE)
                return py_class(self.service, uri)
        else:
            base_uri = self.rdf_post(graph)[0]
            return self.service.get(base_uri)
