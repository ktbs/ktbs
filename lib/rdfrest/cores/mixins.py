#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
I provide additional useful mixin classes to be used with
:class:`local.ILocalCore`.
"""

from itertools import chain
from hashlib import md5 # pylint does not see md5! #pylint: disable=E0611
from logging import getLogger

from time import time

from rdflib import BNode, Graph, Literal, RDF, URIRef, XSD

from ..exceptions import InvalidDataError
from ..util import cache_result, check_new, Diagnosis, parent_uri, replace_node
from .local import compute_added_and_removed, ILocalCore, NS as RDFREST


LOG = getLogger(__name__)

class BookkeepingMixin(ILocalCore):
    """I add bookkeeping metadata to the mixed-in class.

    Bookkeeping metadata consist of:

    * a weak etag (as defined in section 13.3 of :RFC:`2616`)
    * a last-modified data

    .. note::
    
        We are using *weak* etags, because we can not guarantee that
        serializers always give the exact same output for a given graph.
    """

    def iter_etags(self, parameters=None):
        """I return an iterable of the etags of this resource.

        This implementation only yields one etag, regardless of `parameters`,
        but subclasses could override this to yield more, and return different
        etags depending on `parameters`.
        """
        # unused arg `parameter` #pylint: disable=W0613
        yield str(self.metadata.value(self.uri, RDFREST.etag))

    @property
    def last_modified(self):
        """I return the time when this resource was last modified.

        :return: number of seconds since EPOCH, as returned by `time.time()`
        """
        return int(self.metadata.value(self.uri, RDFREST.lastModified))

    @classmethod
    def create(cls, service, uri, new_graph):
        """I override :meth:`.local.ILocalCore.create`
        to generate bookkeeping metadata.
        """
        super(BookkeepingMixin, cls).create(service, uri, new_graph)
        metadata = Graph(service.store, URIRef(uri + "#metadata"))
        cls._update_bk_metadata_in(uri, metadata)
    
    def ack_edit(self, parameters, prepared):
        """I override :meth:`.local.ILocalCore.ack_edit`
        to update bookkeeping metadata.
        """
        super(BookkeepingMixin, self).ack_edit(parameters, prepared)
        self._update_bk_metadata_in(self.uri, self.metadata)

    @classmethod
    def _update_bk_metadata_in(cls, uri, graph):
        """Update the metadata in the given graph.
        """
        now = int(round(time()))
        etag = graph.value(uri, RDFREST.etag)
        token = "%s%s" % (now, etag)
        # NB: using time() only does not always work: time() can return the
        # same value twice; so we salt it with the previous etag (if any),
        # which should do the trick
        new_etag = md5(token).hexdigest()
        graph.set((uri, RDFREST.etag, Literal(new_etag)))
        graph.set((uri, RDFREST.lastModified, Literal(now)))
        # TODO LATER evaluate how slow it is to generate the etag that way,
        # and if a significantly faster way is possible (random_token?)


class FolderishMixin(ILocalCore):
    """I implement :meth:`.interface.ICore.post_graph`.

    This mixin enforces that the resources of this class have a '/'-terminated
    URI.
    """

    @classmethod
    def check_new_graph(cls, service, uri, parameters, new_graph,
                        resource=None, added=None, removed=None):
        """I override :meth:`.local.ILocalCore.check_new_graph`
        to force the URI to end with a '/'.
        """
        diag = super(FolderishMixin, cls) \
            .check_new_graph(service, uri, parameters, new_graph,
                             resource, added, removed)
        if resource is None and uri[-1] != "/":
            diag.append("URI must end with '/'")
        return diag

    @classmethod
    def mint_uri(cls, target, new_graph, created, basename=None, suffix=""):
        """I override :meth:`.local.ILocalCore.mint_uri`
        to force the URI to end with a '/'.
        """
        if suffix[-1:] != "/":
            suffix += "/"
        return super(FolderishMixin, cls) \
            .mint_uri(target, new_graph, created, basename, suffix)


class GraphPostableMixin(ILocalCore):
    """I implement :meth:`.interface.ICore.post_graph`.

    This is a typical implementation where the posted graph represents a single
    resource that will be created as a "child" of this resource. This is why
    this mix-in class should usually be used with :class:`FolderishMixin`.

    In addition to the helper and hook methods defined by
    :class:`.local.ILocalCore`, this mixin class defines a few others that
    are specific to :meth:`post_graph`.
    """

    #
    # Interface implementation
    #

    def post_graph(self, graph, parameters=None,
                   _trust=False, _created=None, _rdf_type=None):
        """I implement :meth:`interface.ICore.post_graph`.

        I will first invoke :meth:`check_parameters`.

        I will then invoke :meth:`find_created` to locate the node to be created
        in the posted graph, and :meth:`check_posted_graph` to check whether the
        posted graph is acceptable. Finally, :meth:`get_created_class` will be
        used to identify the python class of the resource to be created.

        From that class, the following methods will be used (in this order):
        :meth:`mint_uri` to generate the URI of the resource to be created (only
        if it was a BNode in the posted graph);
        :meth:`~.local.ILocalCore.complete_new_graph`, then
        :meth:`~.local.ILocalCore.check_new_graph`, and finally
        :meth:`create`.

        **Optimisation.** If `_created` is provided, :meth:`find_created` will
        not be used. If `_trust` is provided, none of
        :meth:`check_posted_graph`,
        :meth:`~.local.ILocalCore.complete_new_graph` nor
        :meth:`check_new_graph` will be used (in fact,
        `check_posted_graph`:meth: and `check_new_graph`:meth: may be
        `assert`\ ed so that errors are detected earlier. But as `assert`\ s are
        only executed in `__debug__` mode, this should obviously not be relied
        upon).
        """
        self.check_parameters(parameters, "post_graph")

        if _created:
            created = _created
        else:
            created = self.find_created(graph)
            if created is None:
                raise InvalidDataError("Can not find created node")
        if not _trust:
            diag = self.check_posted_graph(parameters, created, graph)
            if not diag:
                raise InvalidDataError(unicode(diag))
        else: # graph is trusted so it SHOULD verify the assert below
            assert self.check_posted_graph(parameters, created, graph), \
                   self.check_posted_graph(parameters, created, graph)

        get_class = self.get_created_class
        if _rdf_type:
            cls = get_class(_rdf_type)
            assert cls is not None
        else:
            cls = None
            for typ in graph.objects(created, RDF.type):
                candidate = get_class(typ)
                if candidate is None:
                    continue
                if cls:
                    raise InvalidDataError("Ambiguous type of posted resource")
                cls = candidate
            if cls is None:
                raise InvalidDataError("No recognized type for posted resource")

        if not isinstance(created, URIRef):
            new_uri = cls.mint_uri(self, graph, created)
            replace_node(graph, created, new_uri)
            created = new_uri
        if not _trust:
            cls.complete_new_graph(self.service, created, None, graph)
            diag = cls.check_new_graph(self.service, created, None, graph)
            if not diag:
                raise InvalidDataError(unicode(diag))
        else: # graph is trusted so it SHOULD verify the assert below
            assert cls.check_new_graph(self.service, created, None, graph), \
                   cls.check_new_graph(self.service, created, None, graph)
        cls.create(self.service, created, graph)

        self.ack_post(parameters, created, graph)
        return [created]
 
    #
    # Hooks and auxiliary method definitions
    #

    def find_created(self, new_graph):
        """Find the node representing the resource to create in `new_graph`.

        :param new_graph: the posted RDF graph
        :type  new_graph: :class:`rflib.Graph`

        :return: the node representing the resource to create, or None if it
                 can not be found.
        :rtype: rdflib.Node

        The default behaviour is to run :meth:`_find_created_default` with a
        query returning all nodes linked to :attr:`~.interface.ICore.uri`.
        Subclasses may also find it useful to rely on
        :meth:`_find_created_default`, passing it a more specific query.
        """
        query = """SELECT ?c 
                   WHERE {{<%s> ?p ?c} UNION {?c ?p <%s>}}"
                """ % (self.uri, self.uri)

        return self._find_created_query(new_graph, query)

    def check_new(self, created):
        """Proxy to :func:`check_new` that can be overrided by children classes."""
        return check_new(self.get_state(), created)

    def check_posted_graph(self, parameters, created, new_graph):
        """Check whether `new_graph` is acceptable to post on this resource.

        Note that the purpose of this method is different from
        :meth:`ILocalCore.check_new_graph`: while the latter implements the
        concerns of the resource to be created, this method implements the
        concerns of the target of the post.

        :param parameters: the query string parameters passed to `post_data`
        :type  parameters: dict or None
        :param created:   the node representing the resource to create
        :type  created:   rdflib.Node
        :param new_graph: the posted RDF graph
        :type  new_graph: rflib.Graph

        :rtype: a `.util.Diagnosis`:class:

        This implementation only checks that the 'created' node is not already
        in use in this resource's graph.
        """
        # unused argument 'new_graph' #pylint: disable=W0613
        diag = Diagnosis("check_posted_graph")
        if isinstance(created, URIRef):
            if not self.check_new(created):
                diag.append("URI already in use <%s>" % created)
        return diag

    def get_created_class(self, rdf_type):
        """Get the python class to use, given an RDF type.

        The default beheviour is to use `self.service.class_map` but some
        classes may override it.
        
        :rtype: a subclass of :class:`~.local.ILocalCore`
        """
        return self.service.class_map.get(rdf_type) 

    def ack_post(self, parameters, created, new_graph):
        """I perform some post processing after a graph has been posted.

        This hook method is called by :meth:`post_graph`;
        calling it directly may *corrupt the service*.

        :param parameters: the query string parameters passed to `post_data`
        :type  parameters: dict or None
        :param created:   the node representing the create resource
        :type  created:   rdflib.Node
        :param new_graph: the posted RDF graph
        :type  new_graph: rflib.Graph

        The default implementation does nothing.
        """
        pass

    #
    # Helper protected methods
    #

    def _find_created_default(self, new_graph, query):
        """I implement a default search algorithm for :meth:`find_create`.

        * all nodes returned by `query` are considered candidates;
        * all literal candidates are discarded;
        * all URI with a fragment id are discarded;
        * all URI that are not a direct child of `self.uri` are discarded
        * at this point, there should be exactly one candidate left

        :param new_graph: the graph to run the query on
        :type  new_graph: :class:`rflib.Graph`
        :param query: a SPARQL SELECT query with exactly one selected variable

        """
        self_uri_str = str(self.uri)
        candidates = []
        for row in new_graph.query(query):
            node = row[0]
            if isinstance(node, BNode):
                candidates.append(node)
            elif isinstance(node, URIRef):
                if "#" not in node  and  parent_uri(node) == self_uri_str:
                    candidates.append(node)
        if len(candidates) != 1:
            LOG.debug("_find_created_candidates: not exactly one candidate: %s",
                      " ".join([ "<%s>" % i for i in candidates ]))
            return None
        return candidates[0]


class WithReservedNamespacesMixin(ILocalCore):
    """ 
    I add reserved namespaces to the mixed-in class.

    A *reserved namespace* is a set of URIs (defined by a common prefix) which
    can not be freely used in the description of the resource, as they have a
    specific meaning for the application.

    Reserved namespaces are listed in the `RDF_RESERVED_NS` class variable (in
    addition to those inherited from superclasses).

    The reserved namespace applies to URIs used as predicates and types.
    The default rule is that they can not be added at creation time (in a graph
    passed to :meth:`~.interface.ICore.post_graph`) nor at
    :meth:`~.interface.ICore.edit` time. They can only be inserted and
    modified by the service itself (i.e. in
    :meth:`~.local.ILocalCore.create` or in a *trusted*
    :meth:`~.local.ILocalCore.edit` contexts).

    It is however possible to provide exceptions for a class, *i.e.* URIs
    inside a reserved namespace which can freely set: at creation time only, or
    at edit time (including creation); as incoming property, outgoing property
    or type. All those exceptions are listed in the corresponding class 
    attributes from the list below (in addition to those inherited from
    superclasses).

    * `RDF_CREATABLE_IN`
    * `RDF_CREATABLE_OUT`
    * `RDF_CREATABLE_TYPES`
    * `RDF_EDITABLE_IN`
    * `RDF_EDITABLE_OUT`
    * `RDF_EDITABLE_TYPES`

    Note that the `RDF_MAIN_TYPE` is always implictly added to
    `RDF_CREATABLE_TYPES` so it is not necessary to specify it there.

    NB: the values of the class attributes are *not* supposed to change over
    time; if they do, the change may not be effective.
    """

    @classmethod
    def check_new_graph(cls, service, uri, parameters, new_graph,
                        resource=None, added=None, removed=None):
        """I overrides :meth:`.local.ILocalCore.check_new_graph`
        to check the reserved namespace constraints.
        """
        if resource is not None:
            old_graph = resource.get_state()
            added, removed = compute_added_and_removed(new_graph, old_graph,
                                                       added, removed)
        diag = super(WithReservedNamespacesMixin, cls) \
            .check_new_graph(service, uri, parameters, new_graph, resource,
                             added, removed)

        if resource is None:
            diag2 = cls.__check_triples(new_graph, "create", uri)
        else:
            triples = chain(removed, added)
            diag2 = cls.__check_triples(triples, "edit", uri)

        return diag & diag2

    #
    # private method
    #

    @classmethod
    @cache_result
    def __get_reserved_namespaces(cls):
        """
        Cache the set of all reserved namespaces.
        """
        return frozenset(
            str(rns)
            for superclass in cls.mro()
            for rns in getattr(superclass, "RDF_RESERVED_NS", ())
            )

    @classmethod
    @cache_result
    def __get_creatable_in(cls):
        """
        Cache the set of all reserved incoming properties allowed at create time.
        """
        return frozenset(chain(
                (
                    prop
                    for superclass in cls.mro()
                    for prop in getattr(superclass, "RDF_CREATABLE_IN", ())
                    ),
                (
                    prop
                    for superclass in cls.mro()
                    for prop in getattr(superclass, "RDF_EDITABLE_IN", ())
                    ),
                ))

    @classmethod
    @cache_result
    def __get_creatable_out(cls):
        """
        Cache the set of all reserved outgoing properties allowed at create time.
        """
        return frozenset(chain(
                (
                    prop
                    for superclass in cls.mro()
                    for prop in getattr(superclass, "RDF_CREATABLE_OUT", ())
                    ),
                (
                    prop
                    for superclass in cls.mro()
                    for prop in getattr(superclass, "RDF_EDITABLE_OUT", ())
                    ),
                ))

    @classmethod
    @cache_result
    def __get_creatable_types(cls):
        """
        Cache the set of all reserved types that can be set at create time.
        """
        return frozenset(chain(
                [cls.RDF_MAIN_TYPE],
                (
                    typ
                    for superclass in cls.mro()
                    for typ in getattr(superclass, "RDF_CREATABLE_TYPES", ())
                    ),
                (
                    typ
                    for superclass in cls.mro()
                    for typ in getattr(superclass, "RDF_EDITABLE_TYPES", ())
                    ),
                ))

    @classmethod
    @cache_result
    def __get_editable_in(cls):
        """
        Cache the set of all editable reserved incoming properties.
        """
        return frozenset(
            prop
            for superclass in cls.mro()
            for prop in getattr(superclass, "RDF_EDITABLE_IN", ())
            )

    @classmethod
    @cache_result
    def __get_editable_out(cls):
        """
        Cache the set of all editable reserved outgoing properties.
        """
        return frozenset(
            prop
            for superclass in cls.mro()
            for prop in getattr(superclass, "RDF_EDITABLE_OUT", ())
            )

    @classmethod
    @cache_result
    def __get_editable_types(cls):
        """
        Cache the set of all editable reserved types.
        """
        return frozenset(
            typ
            for superclass in cls.mro()
            for typ in getattr(superclass, "RDF_EDITABLE_TYPES", ())
            )

    @classmethod
    def __check_triples(cls, triples, operation, uri):
        """Check `triples` respect the reserved namespace constraints.

        :param triples:    an iterable of triples to be changed (created,
                           removed or added)
        :param operation:  "create" or "edit"
        :param uri:        the URI of the resource being created or edited

        :rtype: a `.util.Diagnosis`:class:
        """
        if operation == "create":
            types = cls.__get_creatable_types()
            in_ = cls.__get_creatable_in()
            out = cls.__get_creatable_out()
        else:
            assert operation == "edit"
            types = cls.__get_editable_types()
            in_ = cls.__get_editable_in()
            out = cls.__get_editable_out()

        reserved = cls.__get_reserved_namespaces()
        def is_reserved(a_uri):
            "determine if uri is reserved"
            for i in reserved:
                if a_uri.startswith(i):
                    return True
            return False

        diag = Diagnosis("__check_triples")
        for s, p, o in triples:
            if s == uri:
                if p == RDF.type:
                    if is_reserved(o) and o not in types:
                        diag.append("Can not %s type <%s> for <%s>"
                                   % (operation, o, uri))
                elif is_reserved(p) and p not in out:
                    diag.append( "Can not %s out-property <%s> of <%s>"
                                % (operation, p, uri))
            elif o == uri:
                if is_reserved(p) and p not in in_:
                    diag.append("Can not %s in-property <%s> to <%s>"
                               % (operation, p, uri))
        return diag


class WithCardinalityMixin(ILocalCore):
    """
    I add cardinality constrains on some properties.

    I provide means to express cardinality constraints on some predicate, used
    as incoming and/or outgoing properties, and override `check_new_graph` to
    enforce those constraints.

    Cardinality constraints are listed in the following class variables,
    expressed as tuples of the form (predicate_uri, min_cardinality,
    max_cardinality), respectively for incoming and outgoing
    properties. ``None`` can be used for min_cardinality or max_cardinality to
    mean "no constraint".

    * `RDF_CARDINALITY_IN`
    * `RDF_CARDINALITY_OUT`

    NB: the values of the class variables are *not* supposed to change over
    time; if they do, the change may not be effective.
    """

    @classmethod
    def check_new_graph(cls, service, uri, parameters, new_graph,
                        resource=None, added=None, removed=None):
        """I overrides :meth:`.local.ILocalCore.check_new_graph` to
        check the cardinality constraints.
        """
        diag = super(WithCardinalityMixin, cls).check_new_graph(
            service, uri, parameters, new_graph, resource, added, removed)

        new_graph_subjects = new_graph.subjects
        for p, minc, maxc in cls.__get_cardinality_in():
            nbp = len(list(new_graph_subjects(p, uri)))
            if minc is not None and nbp < minc:
                diag.append("Property <%s> to <%s> should have at least %s "
                              "subjects; it only has %s"
                              % (p, uri, minc, nbp))
            if maxc is not None and nbp > maxc:
                diag.append("Property <%s> to <%s> should have at most "
                              "%s subjects; it has %s"
                              % (p, uri, maxc, nbp))

        new_graph_objects = new_graph.objects
        for p, minc, maxc in cls.__get_cardinality_out():
            nbp = len(list(new_graph_objects(uri, p)))
            if minc is not None and nbp < minc:
                diag.append("Property <%s> of <%s> should have at least "
                              "%s objects; it only has %s"
                              % (p, uri, minc, nbp))
            if maxc is not None and nbp > maxc:
                diag.append("Property <%s> of <%s> should have at most "
                              "%s objects; it has %s"
                              % (p, uri, maxc, nbp))

        return diag

    #
    # private method
    #
    @classmethod
    @cache_result
    def __get_cardinality_in(cls):
        """
        Cache the set of cardinality constraints for incoming properties.
        """
        return frozenset(
            constraint
            for superclass in cls.mro()
            for constraint in getattr(superclass, "RDF_CARDINALITY_IN", ())
            )

    @classmethod
    @cache_result
    def __get_cardinality_out(cls):
        """
        Cache the set of cardinality constraints for outgoing properties.
        """
        return frozenset(
            constraint
            for superclass in cls.mro()
            for constraint in getattr(superclass, "RDF_CARDINALITY_OUT", ())
            )

class WithTypedPropertiesMixin(ILocalCore):
    """
    I add constrains on the datatype of some property values.

    I provide means to force some properties to have only URIs or literals
    as their values, and to constrain the datatype of the said literal.

    Type constraints are listed in the `RDF_TYPED_PROP` class variable,
    expressed as tuples of the form
    `(predicate_uri, node_type[, value_type])`
    where `node_type` is either the string "uri" or the string "literal".
    If `node_type` is "uri" and `value_type` is provided, then it further
    requires the property value to have `node_type` as its ``rdf:type``. 
    If `node_type` is "literal" and `value_type` is provided, then it further
    requires the property value to have `node_type` as its datatype.

    Note that a blank node is acceptable if the node type is "uri", and that
    plain and language-tagged literals are acceptable if the datatype is
    ``xsd:string``.

    Note also that this implementation does no inference on the rdf types not
    on the datatype hierarchy; so the graph must explicitly contain the required
    value type (if any), else it will be rejected.
    """

    @classmethod
    def check_new_graph(cls, service, uri, parameters, new_graph,
                        resource=None, added=None, removed=None):
        """I overrides :meth:`.local.ILocalCore.check_new_graph` to
        check the cardinality constraints.
        """
        diag = super(WithTypedPropertiesMixin, cls).check_new_graph(
            service, uri, parameters, new_graph, resource, added, removed)

        new_graph_objects = new_graph.objects
        in_new_graph = new_graph.__contains__
        for prop, ntype, vtype in cls.__get_typed_prop():
            if ntype == "uri":
                for obj in new_graph_objects(uri, prop):
                    if not (isinstance(obj, URIRef) or isinstance(obj, BNode)):
                        diag.append("Propery <%s> of <%s> expects resources, "
                                    "got literal %s"
                                    % (prop, uri, obj.n3()))
                    elif vtype and not in_new_graph((obj, RDF.type, vtype)):
                        diag.append("Propery <%s> of <%s> expects rdf:type "
                                    "<%s>"
                                    % (prop, uri, vtype))
            else:
                assert ntype == "literal"
                for obj in new_graph_objects(uri, prop):
                    if not isinstance(obj, Literal):
                        diag.append("Propery <%s> of <%s> expects literal, "
                                    "got <%s>"
                                    % (prop, uri, obj))
                    elif vtype and vtype != (obj.datatype or XSD.string):
                        diag.append("Propery <%s> of <%s> expects datatype "
                                    "<%s>, got <%s>"
                                    % (prop, uri, vtype, obj.datatype))
        return diag

    #
    # private method
    #
    @classmethod
    @cache_result
    def __get_typed_prop(cls):
        """
        Cache the set of cardinality constraints for incoming properties.
        """
        return frozenset(
            _normalize_tuple(constraint, 3)
            for superclass in cls.mro()
            for constraint in getattr(superclass, "RDF_TYPED_PROP", ())
            )

# TODO LATER implement WithWatchMixin
# this mix-in class uses three class variables RDF_WATCH_TYPE, RDF_WATCH_IN and
# RDF_WATCH_OUT; it implements prepare_edit and ack_edit; the former memorizes
# in the state of the watches types, incoming properties and outgoing
# properties; in the latter, for each of them that has changed, it calls
# a method ack_watch_X(uri, old_value, new_value)  whete X is 'type', 'in' or
# 'out'. Subclass can then override ack_watch_X to react appropriately to the
# watched change.

# This could replace ad-hoc implementations in example2 (number of tags),
# as well as ktbs.engine.method and ktbs.engine.trace (computed traces).

def _normalize_tuple(atuple, size):
    """Augments the size of `atuple` up to `size`, filling it with None's"""
    missing = size - len(atuple)
    if missing > 0:
        return atuple + missing * (None,)
    else:
        return atuple
