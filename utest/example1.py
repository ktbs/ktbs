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

"""This is simple example of how to use :mod:`rdfrest`.

It describes two kinds of resources, Items and Groups. Items can have a label
(unicode string), a number of tags (unicode strings) and "see also" links to
other (possibly remote) resources. A group is a special item (hence it can have
a label, tags and "see also" links) that can also contain other items.

We first define mix-in classes for Item and Group, relying on the uniform
interface: :class:`ItemMixin` and :class:`GroupMixin`.

We then define local implementations of those resources:
:class:`ItemImplementation` and :class:`GroupImplementation`. Note that those
implementation inherit the mix-in classes defined above, but also override
:class:`rdfrest.local.ILocalResource` methods to check and enforce local
integrity.

We also define custom serializers (HTML view of simple items, and tag list).

We finally define function `main`:func: and auxiliary functions to test this
example.

"""
from nose.tools import assert_raises, eq_ # WTH! #pylint: disable=E0611
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.store import Store
from rdflib.plugin import get as rdflib_plugin_get
from re import compile as RegExp
from sys import argv
from threading import Thread
from time import sleep
from wsgiref.simple_server import make_server

from rdfrest.exceptions import CanNotProceedError
from rdfrest.factory import factory as universal_factory
from rdfrest.http_client import HttpResource
from rdfrest.http_server import HttpFrontend
from rdfrest.interface import register_mixin, IResource
from rdfrest.local import EditableResource, Service
from rdfrest.mixins import FolderishMixin, GraphPostableMixin
from rdfrest.serializers import bind_prefix, register_serializer
from rdfrest.utils import coerce_to_uri, parent_uri

# INTERFACE

EXAMPLE = Namespace("http://example.org/example/")
bind_prefix("ex", "http://example.org/example/")

@register_mixin(EXAMPLE.Item)
class ItemMixin(IResource):
    """Interface of a simple item"""
    
    __state = None

    @property
    def identifier(self):
        """This resource's identifier

        This is last path-element of URI, without the trailing slash if any.
        """
        uri = self.uri
        if uri[-1] == "/":
            uri = uri[:-1]
        return uri.rsplit("/", 1)[1]

    @property
    def state(self):
        """Shortcut to get_state()"""
        ret = self.__state
        if ret is None:
            self.__state = ret = self.get_state()
        return ret

    def _get_label(self):
        """label property implementation"""
        return self.state.value(self.uri, EXAMPLE.label)

    def _set_label(self, value):
        """label property implementation"""
        with self.edit(_trust=True) as editable:
            if value is not None:
                editable.set((self.uri, EXAMPLE.label, Literal(value)))
            else:
                editable.remove((self.uri, EXAMPLE.label, None))

    def _del_label(self):
        """label property implementation"""
        with self.edit(_trust=True) as editable:
            editable.remove((self.uri, EXAMPLE.label, None))

    label = property(_get_label, _set_label, _del_label)
        

    def iter_tags(self):
        """Iter over the tags of this item"""
        for tag in self.state.objects(self.uri, EXAMPLE.tag):
            yield tag

    @property
    def tags(self):
        """List of this item's tags"""
        return set(self.iter_tags())

    def add_tag(self, tag):
        """Add a tag to this item"""
        with self.edit(_trust=True) as graph:
            graph.add((self.uri, EXAMPLE.tag, Literal(tag)))

    def rem_tag(self, tag):
        """Remove a tag from this item"""
        with self.edit(_trust=True) as graph:
            graph.remove((self.uri, EXAMPLE.tag, Literal(tag)))

    def iter_see_alsos(self):
        """Iter over the resources related to this item"""
        for uri in self.iter_see_also_uris():
            res = universal_factory(uri)
            if res is None:
                raise ValueError("Could not make resource <%s>" % uri)
            yield res

    @property
    def see_alsos(self):
        """List of this item's related resources"""
        return set(self.iter_see_alsos())

    def iter_see_also_uris(self):
        """Iter over the URI of the resources related to this item"""
        for uri in self.state.objects(self.uri, EXAMPLE.seeAlso):
            yield uri

    @property
    def see_also_uris(self):
        """List of this item's related resource URIs"""
        return set(self.iter_see_also_uris())

    def add_see_also(self, resource_or_uri):
        """Add a related resource to this item"""
        uri = coerce_to_uri(resource_or_uri, self.uri)
        with self.edit(_trust=True) as graph:
            graph.add((self.uri, EXAMPLE.seeAlso, uri))

    def rem_see_also(self, resource_or_uri):
        """Remove a related resource from this item"""
        uri = coerce_to_uri(resource_or_uri, self.uri)
        with self.edit(_trust=True) as graph:
            graph.remove((self.uri, EXAMPLE.seeAlso, uri))

    @property
    def parent(self):
        """Return the group containing this item (if any)"""
        ret = self.factory(parent_uri(self.uri))
        assert isinstance(ret, GroupMixin)
        return ret

@register_mixin(EXAMPLE.Group)
class GroupMixin(ItemMixin):
    """Interface of a group"""

    ITEM_TYPE = EXAMPLE.Item
    GROUP_TYPE = EXAMPLE.Group

    def __contains__(self, item):
        if isinstance(item, ItemMixin):
            return (self.uri, EXAMPLE.contains, item.uri) in self.state
        else:
            return False

    def __iter__(self):
        return self.iter_items()

    def __len__(self):
        """Return the number of items this group contains"""
        # TODO LATER this would be more efficient with SPARQL 1.1
        ret = 0
        for _ in self.state.objects(self.uri, EXAMPLE.contains):
            ret += 1
        return ret

    def contains_item_with_id(self, ident):
        """Return whethe this group has an item with the given identifier"""
        # we check the ident because an ident including a "/" could provide
        # seemingly correct results
        check_ident(ident)
        item_uri = URIRef(self.uri + ident)
        if (self.uri, EXAMPLE.contains, item_uri) in self.state:
            return True
        # test with group URI
        group_uri = URIRef(item_uri + "/")
        return (self.uri, EXAMPLE.contains, group_uri) in self.state

    def get_item(self, ident):
        """Get an item of this group by its identifier"""
        # we check the ident because an ident including a "/" could provide
        # seemingly correct results
        check_ident(ident)
        item_uri = URIRef(self.uri + ident)
        if not (self.uri, EXAMPLE.contains, item_uri) in self.state:
            item_uri = URIRef(item_uri + "/")
        ret = self.factory(item_uri)
        assert ret is None or isinstance(ret, ItemMixin)
        return ret

    def iter_items(self):
        """Iter over all items in this group"""
        self_factory = self.factory
        for item_uri in self.state.objects(self.uri, EXAMPLE.contains):
            yield self_factory(item_uri)

    @property
    def items(self):
        """List of all items in this group"""
        return set(self.iter_items())

    def iter_simple_items(self):
        """Iter over simple items (i.e. not groups) in this group"""
        query = ("SELECT ?i WHERE { <%s> <%s> ?i. ?i a <%s>. }"
                 % (self.uri, EXAMPLE.contains, self.ITEM_TYPE))
        self_factory = self.factory
        for result in self.state.query(query):
            yield self_factory(result[0], self.ITEM_TYPE)

    @property
    def simple_items(self):
        """List of simple items (i.e. not groups) in this group"""
        return set(self.iter_simple_items())

    def iter_groups(self):
        """Iter over groups in this group"""
        self_factory = self.factory
        graph_contains = self.state.__contains__
        for group_uri in self.state.objects(self.uri, EXAMPLE.contains):
            if graph_contains((group_uri, RDF.type, self.GROUP_TYPE)):
                yield self_factory(group_uri, self.GROUP_TYPE)

    @property
    def groups(self):
        """List of groups in this group"""
        return set(self.iter_groups())
            
    def create_new_simple_item(self, ident):
        """Create a new simple item in this group"""
        check_ident(ident)
        if self.contains_item_with_id(ident):
            raise ValueError("%s already exists" % ident)
        new = Graph()
        created = URIRef(self.uri + ident)
        new.add((self.uri, EXAMPLE.contains, created))
        new.add((created, RDF.type, self.ITEM_TYPE))
        uris = self.post_graph(new, None, True, created, self.ITEM_TYPE)
        assert len(uris) == 1
        ret = self.factory(uris[0], self.ITEM_TYPE)
        assert isinstance(ret, ItemMixin)
        return ret

    def create_new_group(self, ident):
        """Create a new group in this group"""
        check_ident(ident)
        if self.contains_item_with_id(ident):
            raise ValueError("%s already exists" % ident)
        new = Graph()
        created = URIRef(self.uri + ident + "/")
        new.add((self.uri, EXAMPLE.contains, created))
        new.add((created, RDF.type, self.GROUP_TYPE))
        uris = self.post_graph(new, None, True, created, self.GROUP_TYPE)
        assert len(uris) == 1
        ret = self.factory(uris[0], self.GROUP_TYPE)
        assert isinstance(ret, GroupMixin)
        return ret

    def remove_item(self, ident):
        """Remove an item from this group"""
        # we check the ident because an ident including a "/" could provide
        # seemingly correct results
        check_ident(ident)
        item = self.get_item(ident)
        if item is None:
            return
        item.delete() # do not trust; we leave it to the implementation to
                      # check whether this is possible
        self.force_state_refresh()


# IMPLEMENTATION

_IDENT_RE = RegExp("[a-zA-Z_0-9]+\Z")

def check_ident(ident):
    """Check whether an identifier is syntactically valid"""
    if not _IDENT_RE.match(ident):
        raise ValueError("Invalid identifier '%s'" % ident)

class ItemImplementation(ItemMixin, EditableResource):
    """Implementation of Item resource"""

    BASENAME = "item"
    RDF_MAIN_TYPE = EXAMPLE.Item

    @classmethod
    def mint_uri(cls, target, new_graph, created, basename=None, suffix=""):
        """I overrides :meth:`.local.ILocalResource.mint_uri`

        to use cls.BASENAME instead of cls.__classname__.
        """
        return super(ItemImplementation, cls) \
            .mint_uri(target, new_graph, created, cls.BASENAME, suffix)

    @classmethod
    def check_new_graph(cls, service, uri, parameters, new_graph,
                        resource=None, added=None, removed=None):
        """I implement :meth:`rdfrest.local.ILocalResource.check_new_graph`
        """
        diag = super(ItemImplementation, cls).check_new_graph(
            service, uri, parameters, new_graph, resource, added, removed)
        if not (uri, RDF.type, cls.RDF_MAIN_TYPE) in new_graph:
            diag.append("Expected rdf:type <%s>" % cls.RDF_MAIN_TYPE)
        return diag 

    def ack_delete(self, parameters):
        """I implement :meth:`rdfrest.local.EditableResource.ack_delete`.
        """
        super(ItemImplementation, self).ack_delete(parameters)
        parent = self.parent
        if parent is not None:
            with parent.edit(_trust=True) as graph:
                graph.remove((parent.uri, EXAMPLE.contains, self.uri))
                graph.remove((self.uri, RDF.type, self.RDF_MAIN_TYPE))

class GroupImplementation(GroupMixin, FolderishMixin, GraphPostableMixin,
                          ItemImplementation):
    """Implementation of Group resource"""

    BASENAME = "group"
    RDF_MAIN_TYPE = EXAMPLE.Group

    def find_created(self, new_graph):
        """I implement :meth:`rdfrest.local.GraphPostableMixin.find_created`.
        """
        query = ("SELECT ?c WHERE { <%s> <%s> ?c }" 
                 % (self.uri, EXAMPLE.contains))
        return self._find_created_default(new_graph, query)

    def check_posted_graph(self, parameters, created, new_graph):
        """I implement
        :meth:`rdfrest.local.GraphPostableMixin.check_posted_graph`.
        """
        diag = super(GroupImplementation, self) \
            .check_posted_graph(parameters, created, new_graph)
        if isinstance(created, URIRef):
            if not created.startswith(self.uri):
                diag.append("The URI of the created item is not consistent "
                            "with the URI of this group <%s>" % created)
            else:
                ident = created[len(self.uri):]
                if ident[-1] == "/":
                    ident = ident[:-1]
                if not _IDENT_RE.match(ident):
                    diag.append("The identifier of the created item is "
                                "invalid: [%s]" % ident)
                elif (self.uri, EXAMPLE.contains, created) in self.state:
                    diag.append("Item already exists <%s>" % created)
        return diag

    def ack_post(self, _parameters, created, new_graph):
        """I implement :meth:`rdfrest.local.GraphPostableMixin.ack_post`.
        """
        rdf_type = new_graph.value(created, RDF.type)
        with self.edit(_trust=True) as graph:
            graph.add((self.uri, EXAMPLE.contains, created))
            graph.add((created, RDF.type, rdf_type))

    def check_deletable(self, parameters):
        """I implement :meth:`rdfrest.local.EditableResource.check_deletable`.
        """
        diag = super(GroupImplementation, self).check_deletable(parameters)
        if self.uri == self.service.root_uri:
            diag.append("Can not delete root group")
        if len(self) > 0:
            diag.append("Can not delete non-empty group")
        return diag

    @classmethod
    def create_service_root(cls, service):
        """Create a root-group in given service"""
        root_uri = service.root_uri
        graph = Graph(identifier=root_uri)
        graph.add((root_uri, RDF.type, cls.RDF_MAIN_TYPE))
        cls.create(service, root_uri, graph)
        

@register_serializer("text/html", "htm", 90, EXAMPLE.Item)
def serialize_item_in_html(resource, _parameters=None, _bindings=None,
                           _base_uri=None):
    """A dedicated HTML view of simple items"""
    assert resource.RDF_MAIN_TYPE == EXAMPLE.Item
    values = {
        "identifier": resource.identifier.encode("utf-8"),
        }
    yield """<!DOCTYPE html>
    <html>
        <head><title>Item %(identifier)s</title></head>
        <body>
            <section><h1>Item %(identifier)s</h1>
                <section><h2>Tags</h2>
                    <ul>""" % values

    for i in resource.iter_tags():
        yield """
                        <li>%s</li>""" % i.encode("utf-8")
    yield """
                    </ul>
                </section>
                <section><h2>See also</h2>
                    <ul>"""
    for i in resource.iter_see_also_uris():
        yield """
                        <li><a href="%s">%s</a></li>""" \
            % (str(i), str(i))
    yield """
                </section>
            </section>
            <footer><a href="%s.html">See default HTML view</a></footer>
        </body>
    </html>\n""" % str(resource.uri)


@register_serializer("text/tags", None, 20)
@register_serializer("text/plain", "tags", 15)
def serialize_tags(resource, _parameters=None, _bindings=None, _base_uri=None):
    """A dedicated format exporting only the list of tags"""
    return ( i.encode("utf-8")+"\n" for i in resource.tags )


# MAIN FUNCTION AND TESTS

def main():
    """Runs an HTTP server serving items and groups.

    If 'test' is passed as argument, first run :func:`do_tests` on both a
    local service and through HTTP.
    """
    test = len(argv) > 1 and argv[1] == "test"

    root_uri = URIRef("http://localhost:1234/foo/")
    serv = make_example1_service(root_uri)

    if test:
        local_root = serv.get(root_uri)
        assert isinstance(local_root, GroupImplementation)
        do_tests(local_root)
        print "Local tests passed"

    thread, _httpd = make_example1_httpd(serv)
    try:
        if test:
            remote_root = HttpResource.factory(root_uri, EXAMPLE.Group)
            assert isinstance(remote_root, GroupMixin)
            do_tests(remote_root)
            print "Remote tests passed"
        print "Now listening on", root_uri
        sleep(3600) # allows to catch KeyboardInterrupt (thread.join doesn't)
        thread.join() # prevents 'finally' clause if sleep above expires
    finally:
        _httpd.shutdown()
        print "httpd stopped"

def make_example1_service(root_uri, store=None):
    """Make a service serving items and groups."""
    if store is None:
        store = rdflib_plugin_get("IOMemory", Store)()
    return Service(root_uri, store, [ItemImplementation, GroupImplementation],
                   GroupImplementation.create_service_root)

def do_tests(root):
    """Test items and groups implementations.

    Populate root with items and sub-groups, trying to be exhaustive in the
    tested functionalities.

    Then cleans everything.
    """
    check_content(root, [])
    item1 = root.create_new_simple_item("item1")
    check_content(root, [item1])
    test_label_and_tags(item1)

    item2 = root.create_new_simple_item("item2")
    check_content(root, [item1, item2])
    test_label_and_tags(item2)

    group1 = root.create_new_group("group1")
    check_content(root, [item1, item2, group1])
    test_label_and_tags(group1)
    check_content(group1, [])

    item11 = group1.create_new_simple_item("item1")
    check_content(root, [item1, item2, group1])
    check_content(group1, [item11])
    test_label_and_tags(item11)

    eq_(item1.identifier, item11.identifier)
    eq_(group1.identifier, "group1")
    assert item1  in root   and  item1  not in group1
    assert item11 in group1 and  item11 not in root

    # test the _no_spawn argument in factory
    item1bis = root.factory(URIRef("item1", root.uri))
    assert item1bis is item1
    item1bis = root.factory(URIRef("item1", root.uri), _no_spawn=True)
    assert item1bis is item1
    del item1, item1bis
    item1 = root.factory(URIRef("item1", root.uri), _no_spawn=True)
    assert item1 is None

    
    # clean everything
    root.remove_item("item1")
    check_content(root, [item2, group1])
    root.remove_item("item1") # removing item twice
    check_content(root, [item2, group1])
    root.remove_item("item3") # removing non-exitsing item
    check_content(root, [item2, group1])
    root.remove_item("item2")
    check_content(root, [group1])
    with assert_raises(CanNotProceedError):
        root.remove_item("group1")
    group1.remove_item("item1")
    check_content(group1, [])
    root.remove_item("group1")
    check_content(root, [])

def make_example1_httpd(service=None):
    """Make a HTTPd running in a separate thread.

    Return the thread and the HTTPd.

    :param service: if provided

    NB: the service is assumed to be located on localhost:1234
    """
    if service is None:
        service = make_example1_service("http://localhost:1234/foo")
    app = HttpFrontend(service, cache_control="max-age=60")
    _httpd = make_server("localhost", 1234, app)
    thread = Thread(target=_httpd.serve_forever)
    thread.start()
    return thread, _httpd

def check_content(group, ref_items):
    """Checks the content of a group against a reference list"""
    ref_items = set(ref_items)
    eq_(group.items, ref_items)
    eq_(len(group), len(ref_items))
    eq_(group.simple_items,
        set( i for i in ref_items if not isinstance(i, GroupMixin) ))
    eq_(group.groups,
        set( i for i in ref_items if isinstance(i, GroupMixin) ))

    for i in group:
        assert i in group
        assert group.contains_item_with_id(i.identifier)
        eq_(i.parent, group)
        eq_(group.get_item(i.identifier), i)

def test_label_and_tags(item):
    """Test label- and tag-related functionalities on item"""
    # label
    assert item.label is None
    item.label = "hello world"
    assert item.label == Literal("hello world")
    item.label = "bonjour le monde"
    assert item.label == Literal("bonjour le monde")
    item.label = None
    assert item.label is None
    item.label = "Halo Welt"
    assert item.label == Literal("Halo Welt")
    del item.label
    assert item.label is None
    # adding tags
    eq_(item.tags, set([]))
    item.add_tag(u"tag1")
    eq_(item.tags, set([Literal("tag1")]))
    item.add_tag(u"tag1")
    eq_(list(item.iter_tags()), [Literal("tag1")]) # tags do not duplicate
    item.add_tag(u"tag2")
    eq_(item.tags, set([Literal("tag1"), Literal("tag2")]))
    item.add_tag(u"tag3")
    eq_(item.tags, set([Literal("tag1"), Literal("tag2"), Literal("tag3")]))
    # removing tags
    item.rem_tag(u"tag2")
    eq_(item.tags, set([Literal("tag1"), Literal("tag3")]))
    item.rem_tag(u"tag2") # removing tag twice has no effect
    eq_(item.tags, set([Literal("tag1"), Literal("tag3")])) 
    item.rem_tag(u"tag4") # removing inexisting tag has no effect
    eq_(item.tags, set([Literal("tag1"), Literal("tag3")])) 
    # unicode tags
    item.add_tag(u"tagué")
    eq_(item.tags, set([Literal("tag1"), Literal("tag3"), Literal(u"tagué")])) 


if __name__ == "__main__":
    main()
