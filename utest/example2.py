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

"""
I extend classes from :mod:`.example1` with mixins from :mod:`rdfrest.mixins`.

While we are inheriting the mix-in classes from example1, we are redefining
implementation classes from scratch.

Item2 supports the following parameters:
* 'valid=x' for all verbs on all resources (does nothing)
* 'notallowed=x' for all verbs on all resources (raises MethodNotAllowed)
* 'redirect=x' for GET (redirects to relative URI x)

Finally, the service provided by this module  supports a pseudo item '@goto' of
the root, that redirects to the root.
"""

from rdflib import Literal, Graph, URIRef, XSD
from rdflib.store import Store
from rdflib.plugin import get as rdflib_plugin_get
from sys import argv
from wsgiref.simple_server import make_server

from rdfrest.exceptions import MethodNotAllowedError
from rdfrest.http_server import HttpFrontend
from rdfrest.interface import register_mixin
from rdfrest.local import Service
from rdfrest.mixins import BookkeepingMixin, WithCardinalityMixin, \
    WithReservedNamespacesMixin, WithTypedPropertiesMixin
from rdfrest.utils import ReadOnlyGraph

from example1 import do_tests, EXAMPLE, GroupImplementation, GroupMixin, \
    ItemImplementation, ItemMixin

# ex:Item2 has the same API as ex:Item
register_mixin(EXAMPLE.Item2)(ItemMixin)

@register_mixin(EXAMPLE.Group2)
class Group2Mixin(GroupMixin):
    """Interface definition of Group2.

    It is identical to Group, but for its ITEM_TYPE and GROUP_TYPE.
    """

    ITEM_TYPE = EXAMPLE.Item2
    GROUP_TYPE = EXAMPLE.Group2


class Item2Implementation(BookkeepingMixin, WithCardinalityMixin,
                          WithReservedNamespacesMixin, WithTypedPropertiesMixin,
                          ItemImplementation):
    """Item2 implementation"""

    RDF_MAIN_TYPE = EXAMPLE.Item2

    RDF_RESERVED_NS =     [EXAMPLE]
    RDF_CREATABLE_IN =    [EXAMPLE.contains]
    RDF_CREATABLE_OUT =   []
    RDF_CREATABLE_TYPES = []
    RDF_EDITABLE_IN =     []
    RDF_EDITABLE_OUT =    [EXAMPLE.label, EXAMPLE.tag, EXAMPLE.seeAlso]
    RDF_EDITABLE_TYPES =  []

    RDF_CARDINALITY_OUT = [(EXAMPLE.label, 0, 1)]

    RDF_TYPED_PROP = [(EXAMPLE.label,   "literal", XSD.string),
                      (EXAMPLE.tag,     "literal", XSD.string),
                      (EXAMPLE.seeAlso, "uri"),
                      ]

    @classmethod
    def create(cls, service, uri, new_graph):
        """I implement :meth:`ILocalResource.create`.

        I update the special property number_of_tags"""
        tag_nb = 0
        for _ in new_graph.triples((uri, EXAMPLE.tag, None)):
            tag_nb += 1
        new_graph.add((uri, EXAMPLE.number_of_tags, Literal(tag_nb)))
        super(Item2Implementation, cls).create(service, uri, new_graph)

    def check_parameters(self, parameters, method):
        """I accept the accepted parameters"""
        if parameters:
            if "notallowed" in parameters:
                raise MethodNotAllowedError("Parameter notallowed was used")
            parameters.pop("valid", None)
            # we do not pop redirect_to, as it is handled by get_state
            # *before* check_parameters is even called
        if not parameters:
            parameters = None
        super(Item2Implementation, self).check_parameters(parameters,
                                                          method)

    def get_state(self, parameters=None):
        """I enforce a redirection if parameter `redirect` is provided."""
        target_uri = parameters and parameters.pop("redirect", None) or None
        if target_uri is None:
            ret = super(Item2Implementation, self).get_state(parameters)
        else:
            target_uri = URIRef(target_uri, self.uri)
            target = self.factory(target_uri)
            if target is None:
                ret = Graph(identifier=target_uri)
            else:
                ret = ReadOnlyGraph(target.get_state(parameters))
            ret.redirect_to = str(target_uri)
        return ret
                
    def ack_edit(self, parameters, prepared):
        """I override :meth:`rdfrest.local.EditableMixin.ack_edit`

        I update the special property number_of_tags"""
        super(Item2Implementation, self).ack_edit(parameters, prepared)
        with self.edit(_trust=True) as graph:
            graph.set((self.uri, EXAMPLE.number_of_tags,
                       Literal(len(self.tags))))


class Group2Implementation(Group2Mixin,
                           Item2Implementation, GroupImplementation
                           # inheriting two implementation is ugly,
                           # but Item2Implementation is in fact a mix-in
                           ):
    """Group2 implementation"""

    RDF_MAIN_TYPE = EXAMPLE.Group2


class Ex2Service(Service):
    """I override Service.get to support some parameters (see module doc)"""
    # too few public methods (1/2) #pylint: disable=R0903
    def get(self, uri, _rdf_type=None, _no_spawn=False):
        """I override Service.get"""
        ret = super(Ex2Service, self).get(uri, _rdf_type, _no_spawn)
        if ret is None:
            if uri == URIRef("@proxy", self.root_uri):
                ret = super(Ex2Service, self).get(self.root_uri, _rdf_type,
                                                  _no_spawn)
        return ret
        

def main():
    """Runs an HTTP server serving items and groups.

    If 'test' is passed as argument, first run :func:`do_tests` from
    :mod:`.example1` on the service.
    """
    test = len(argv) > 1 and argv[1] == "test"

    root_uri = URIRef("http://localhost:1234/foo/")
    serv = make_example2_service(root_uri)

    if test:
        do_tests(serv.get(root_uri))
        print "Local tests passed"

    app = HttpFrontend(serv)
    _httpd = make_server("localhost", 1234, app)
    print "Now listening on", root_uri
    _httpd.serve_forever()

def make_example2_service(root_uri, store=None, additional=()):
    """Make a service serving item2's and group2's.

    Additional classes can also be passed.
    """
    if store is None:
        store = rdflib_plugin_get("IOMemory", Store)()
    additional = list(additional)
    return Ex2Service(root_uri, store,
                      [Item2Implementation, Group2Implementation] + additional,
                      Group2Implementation.create_service_root)


if __name__ == "__main__":
    main()
