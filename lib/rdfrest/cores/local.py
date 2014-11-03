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
I provide a local implementation of `.interface.ICore`:class:.

"Local" means either standalone or server-side. The difference with a "remote"
implementation (*e.g.* client-side) is that the local implementation must
implement the concerns of the server.

* A :class:`Service` is the central component managing a set of local resources
  with a common URI prefix (the service's root). When initialized, a service is
  passed a list of the `~.interface.ICore`:class: implementations it will
  manage.

* More precisely, the classes passed to a `Service`:class: must implement
  :class:`ILocalCore`, a sub-interface of `~.interface.Resource`:class:
  augmenting it with attributes and hooks methods aimed at managing the concerns
  of the server (integrity checking, update propagations...).

* This module provides default implementations of :class:`ILocalCore`:
  :class:`LocalCore` (supporting only "read" operations) and
  :class:`EditableCore` (supporting :meth:`~.interface.Resource.edit` and
  :meth:`~.interface.Resource.delete`).

* Subclasses of :class:`ILocalCore` can also benefit from a number of mix-in
  classes provided in the `.mixins`:mod: module.
"""
from contextlib import contextmanager
import traceback
from weakref import WeakValueDictionary

from os.path import exists
from rdflib import Graph, plugin as rdflib_plugin, Namespace, RDF, RDFS, URIRef
from rdflib.store import Store
from rdflib.compare import graph_diff

from ..exceptions import CanNotProceedError, InvalidDataError, \
    InvalidParametersError, MethodNotAllowedError, RdfRestException
from .factory import register_service, unregister_service
from .hosted import HostedCore
from ..cores import ICore
from ..wrappers import get_wrapped
from ..util import coerce_to_uri, Diagnosis, make_fresh_uri, ReadOnlyGraph, \
    urisplit
from ..util.config import get_service_configuration, build_service_root_uri
from ..util.config import apply_logging_config


NS = Namespace("tag:silex.liris.cnrs.fr.2012.08.06.rdfrest:")


################################################################
#
# Service
#

class Service(object):
    """I manage a set of related :class:`ILocalCore`'s.

    All the resources in a service are stored in the same
    `rdflib.store.Store`:class:.

    :param classes: a list of classes to be used by this service (see below)
    :param service_config: kTBS configuration
    :param init_with: a callable to initialize the store if necessary (i.e. at
        least populate the root resource); it will be passed this service as
        its sole argument.

    root_uri (str), the URI of the root resource of this service
    store (rdflib.store.Store), the RDF store containing the data of this service
    init_with, a callable to initialize the store if necessary (i.e. at
    least populate the root resource); it will be passed this service as
    its sole argument.

    The classes passed to this service should all be subclasses of
    :class:`ILocalCore`, and all have an attribute `RDF_MAIN_TYPE`
    indicating the RDF type they implement.
    """
    # too few public methods (1/2) #pylint: disable=R0903

    def __init__(self, classes, service_config=None, init_with=None):
        """I create a local RDF-REST service around the given store.
        """
        if service_config is None:
            service_config = get_service_configuration()

        self.config = service_config
        root_uri = build_service_root_uri(service_config)

        assert urisplit(root_uri)[3:] == (None, None), \
            "Invalid URI <%s>" % root_uri
        self.root_uri = coerce_to_uri(root_uri)

        apply_logging_config(service_config)

        init_repo = False
        repository = service_config.get('rdf_database', 'repository', 1)
        if not repository:
            init_repo = True
            repository = ":IOMemory:"
        elif repository[0] != ":":
            init_repo = not exists(repository)
            repository = ":Sleepycat:%s" % repository

        # Whether we should force data repository initialization
        if service_config.getboolean('rdf_database', 'force-init'):
            init_repo = True

        _, store_type, config_str = repository.split(":", 2)
        store = rdflib_plugin.get(store_type, Store)(config_str)

        self.store = store
        self.class_map = class_map = {}
        for cls in classes:
            assert issubclass(cls, ILocalCore)
            assert cls.RDF_MAIN_TYPE not in class_map, \
                "duplicate RDF_MAIN_TYPE <%s>" % cls.RDF_MAIN_TYPE
            class_map[cls.RDF_MAIN_TYPE] = cls

        # about self._resource_cache: this is not per se a cache,
        # but ensures that we will not generate multiple instances for the
        # same resource.
        self._resource_cache = WeakValueDictionary()
        self._context_level = 0

        root_metadata_uri = URIRef(root_uri + "#metadata")
        metadata_graph = Graph(store, root_metadata_uri)
        initialized = list(metadata_graph.triples((self.root_uri,
                                                   NS.hasImplementation,
                                                   None)))
        if not initialized and init_repo:
            assert init_with, \
                "Store is not initialized, and no initializer was provided"
            init_with(self)
            assert (list(metadata_graph.triples((self.root_uri,
                                                 NS.hasImplementation,
                                                 None)))) # correctly init'ed
            
        register_service(self)

    def __del__(self):
        try:
            unregister_service(self)
        except BaseException:
            pass

    @HostedCore.handle_fragments
    def get(self, uri, _rdf_type=None, _no_spawn=False):
        """Get a resource from this service.

        :param uri:      the URI of the resource
        :type  uri:      :class:`~rdflib.URIRef`
        :param _rdf_type: a hint at the expected RDF type of the resource
        :type  _rdf_type: :class:`~rdflib.URIRef`
        :param _no_spawn: if True, only *pre-existing* python objects will be
                          returned
        :type  _no_spawn: bool

        :return: the resource, or None
        :rtype:  :class:`ILocalCore` or :class:`~.cores.hosted.HostedCore`

        TODO NOW: if no resource is found, try to get it from parent resource

        NB: if uri contains a fragment-id, the returned resource will be a
        `~.cores.hosted.HostedCore`:class: hosted by a resource from this
        service.

        When using this function, it is a good practice to indicate the expected
        return type, either informally (with a comment) or formally, with a
        statement of the form::
    
            assert isinstance(returned_object, expected_class)
        """
        assert isinstance(uri, URIRef)
        querystr, fragid = urisplit(uri)[3:]
        if querystr is not None  or  fragid is not None:
            # fragid is managed by the decorator HostedCore.handle_fragment
            return None
        resource = self._resource_cache.get(uri)
        if resource is None  and  not _no_spawn:
            # find base rdf:type
            metadata = Graph(self.store, URIRef(uri + "#metadata"))
            if len(metadata) == 0:
                return None
            if _rdf_type:
                assert (uri, NS.hasImplementation, _rdf_type) in metadata
                typ = _rdf_type
            else:
                types = list(
                    metadata.objects(uri, NS.hasImplementation))
                assert len(types) == 1, types
                typ = types[0]
            # find base python class
            py_class = self.class_map.get(typ)
            if py_class is None:
                raise ValueError("No implementation for type <%s> of <%s>"
                                 % (types[0], uri))
            # derive subclass bas
            graph = Graph(self.store, uri)
            types = [ i for i in graph.objects(uri, RDF.type) if i != typ ]
            py_class = get_wrapped(py_class, types)
            # make resource and store it in "cache"
            resource = py_class(self, uri)
            self._resource_cache[uri] = resource
        return resource

    def __enter__(self):
        """Start to modifiy this service.

        The role of using a service as a context is to ensure that data is
        correctly handled by the underlying RDF store:

        * on normal exit,
        :meth:`self.store.commit <rdflib.store.Store.commit>` will be called.
        
        * if an exception is raised,
        :meth:`self.store.rollback <rdflib.store.Store.rollback>` will be
        called.

        * if several contexts are embeded (e.g. by calling a function that
        itself uses the service context), the commit/rollback will only occur
        when exiting the *outermost* context, ensuring that only globally
        consistent states are commited.
    
        Note that the implementations provided in this module already take care
        of using the service context, so implementors relying them should not
        have to worry about it. It may be necessary to explicitly call the
        service context, though, to make a set of resource modifications aromic.

        .. warning::

            For the moment (2012-07), most implementations of
            :class:`rdflib.store.Store` do not support rollback (which simply
            does nothing). So unless you know for sure that the store you are
            using does support rollback, you should assume that the store is
            corrupted when exiting abnormally from the service context.
        """
        self._context_level += 1

    def __exit__(self, typ, _value, _traceback):
        """Ends modifications to this service.
        """
        level = self._context_level - 1
        self._context_level = level
        if level == 0:
            if typ is None:
                self.store.commit()
            else:
                self.store.rollback()
                # we rollback *in case* the store supports it,
                # to try to restore it in a consistent state.
                # However there is no guarantee that this work,
                # as not all stores support rollback.
                # This is therefore a best-effort to limit damages,
                # rather than a safe handling of the exception
                # (at least, until all stores support rollback).
                return False


################################################################
#
# :class:`.interface.ICore` implementation.
#

class ILocalCore(ICore):
    """
    A RESTful resource implemented by a local :class:`Service`.

    I merely define the interface that service resources must implement,
    in addition to implementing :class:`.interface.ICore`.

    The attributes and methods it defines must, of course, be only used in
    implementation-related code; API-related code must only rely on the uniform
    interface of :class:`.interface.ICore`.

    .. py:attribute:: service

        The :class:`Service` this resource depends on.

    """

    def check_parameters(self, parameters, method):
        """I checks whether parameters are acceptable.

        This hook method is to be called whenever a method from
        :class:`.interface.ICore` is invoked, and raises an
        `~.exceptions.InvalidParametersError`:class: if the given
        parameters are not acceptable for the given method.

        NB: an empty dict means that an empty query string has been appended
        to the original URI (trailing ``?``), while None means no query string
        at all.

        :param parameters: the query string parameters passed to `edit` if any
        :type  parameters: dict or None
        :param method:     the name of the calling python method
        :type  method:     unicode

        :raise: `.exceptions.InvalidParametersError`:class:
        """
        raise NotImplementedError

    @classmethod
    def complete_new_graph(cls, service, uri, parameters, new_graph,
                           resource=None):
        """I alter a graph for representating a resource of this class.
        
        This hook method is to be called when a resource of this class is
        either created and updated, before :meth:`check_new_graph` is called.

        :param service:    the service to which `new_graph` has been posted
        :type  service:    :class:`Service`
        :param uri:        the URI of the resource described by `new_graph`
        :type  uri:        :class:`rdflib.URIRef`
        :param parameters: the query string parameters passed to `edit` if any
        :type  parameters: dict or None
        :type  new_graph:  :class:`rdflib.Graph`
        :param new_graph:  graph to check
        :type  new_graph:  :class:`rdflib.Graph`

        The following parameter will always be set  when `complete_new_graph` is
        used to update and *existing* resource; for creating a new resource, it
        will always be `None`.

        :param resource:  the resource to be updated

        This class method can be overridden by subclasses tat have need to
        automatically generate or update parts of their representation.
        """
        raise NotImplementedError

    @classmethod
    def check_new_graph(cls, service, uri, parameters, new_graph,
                        resource=None, added=None, removed=None):
        """I check that a graph is a valid representation for a resource.

        This hook method is to be called when a resource of this class is
        either created and updated, to verify if `new_graph` is acceptable.

        :param service:    the service to which `new_graph` has been posted
        :type  service:    :class:`Service`
        :param uri:        the URI of the resource described by `new_graph`
        :type  uri:        :class:`rdflib.URIRef`
        :param parameters: the query string parameters passed to `edit` if any
        :type  parameters: dict or None
        :type  new_graph:  :class:`rdflib.Graph`
        :param new_graph:  graph to check
        :type  new_graph:  :class:`rdflib.Graph`

        The following parameter will always be set when `check_new_graph` is
        used to update and *existing* resource; for creating a new resource, it
        will always be `None`.

        :param resource:  the resource to be updated

        The following parameters only make sense when updating an existing
        resource. They are *not* automatically set by `edit`:meth:, as they may
        not be used. However, any implementation may set them by using
        :func:`compute_added_and_removed` and should therefore pass them along
        the `super` calls.

        :param added:     if not None, an RDF graph containg triples to be
                          added
        :param removed:   if not None, an RDF graph containg triples to be
                          removed

        The return value should be an empty `~.util.Diagnosis`:class: if the
        new graph is acceptable, else it should contain a description of the
        problem(s).

        :rtype: `~.util.Diagnosis`:class:
        """
        raise NotImplementedError

    @classmethod
    def mint_uri(cls, target, new_graph, created, basename=None, suffix=""):
        """I mint a fresh URI for a resource of that class.

        This method is called by :class:`rdfrest.cores.mixins.GraphPostableMixin`;
        calling it directly is usually not required.

        :param target:    the resource to which `new_graph` has been posted
        :type  target:    :class:`ILocalCore`
        :param new_graph: a description of the resource for which to mint a URI
        :type  new_graph: rdflib.Graph
        :param created:   the non-URIRef node representing the resource in
                          $`new_graph`
        :type  created:   rdflib.Node
        :param basename:  a base on which the last part of the URI will be
                          generated
        :type  basename:  str
        :param suffix:    a string that will be added at the end of the URI
        :type  suffix:    str

        :rtype: rdflib.URIRef
        """
        raise NotImplementedError

    @classmethod
    def create(cls, service, uri, new_graph):
        """I create a resource of this class in `service`.

        This method is responsible of actually storing the resource in the
        service.

        :param service:   the service in which to create the resource
        :type  service:   :class:`Service`
        :param uri:       the URI of the resource to create
        :type  uri:       :class:`rdflib.URIRef`
        :param new_graph: RDF data describing the resource to create;
                          it is assumed to have passed :meth:`check_new_graph`
        :type  new_graph: :class:`rdflib.Graph`
        """
        raise NotImplementedError

    def prepare_edit(self, parameters):
        """I perform some pre-processing before editing this resource.

        I return an object that will be passed to :meth:`ack_edit`
        as parameter `prepared`.
        This object can be used to cache
        some information from the original state
        that will be required by :meth:`ack_edit`.
        
        This hook method is to be called on entering the :meth:`edit` context.

        :param parameters: the query string parameters passed to `edit` if any
        :type  parameters: dict or None

        :rtype: a mutable object
        """
        raise NotImplementedError

    def ack_edit(self, parameters, prepared):
        """I perform some post-processing after editing this resource.

        This hook method is to be called when exiting the :meth:`edit` context;
        calling it directly may *corrupt the service*.

        :param parameters: the query string parameters passed to `edit` if any
        :type  parameters: dict or None
        :param prepared:   the object returned by :meth:`prepare_edit`

        Note to implementors: :meth:`ack_edit` may alter the state of
        the resource using the :meth:`edit` context, but is required to pass
        True to its `_trust` parameter, leaving you the responsibility of
        maintaining the integrity of the resource's state).
        """
        raise NotImplementedError

    def check_deletable(self, parameters):
        """I check that this resource can safely be deleted.

        This hook method is to be called on entering the :meth:`delete` method.

        :param parameters: the querystring parameters passed to `delete` if any
        :type  parameters: dict or None

        :rtype: `.util.Diagnosis`:class:

        This class method can be overridden by subclasses that have constraints
        on whether their instances can be deleted.
        """
        raise NotImplementedError

    def ack_delete(self, parameters):
        """I perform some post processing after deleting this resource.

        This hook method is to be called on exiting the :meth:`delete` method;
        calling it directly may *corrupt the service*.

        :param parameters: the querystring parameters passed to `delete` if any
        :type  parameters: dict or None

        Note to implementors: this method is actually called *just before* the
        public and metadata graphs of this resource are emptied, so all the
        information is still available to this method. Care should nonetheless
        be taken not to call methods that might alter other resources as if
        this one was to continue existing.
        """
        raise NotImplementedError


class LocalCore(ILocalCore):
    """I provide a default implementation of :class:`ILocalCore`.

    The state of a local core is stored in the service's store
    as an individual graph, identified by the resource's URI.

    .. attribute:: metadata

        A graph containing some metadat about this resource, for internal use
        (not exposed by :meth:`~interface.ICore.get_state`).

    .. method:: __init__(service, uri, graph_uri=None)

        :param service: the service this resource depends on
        :type  service: :class:`Service`
        :param uri:     the URI of this resource
        :type  uri:     :class:`rdflib.URIRef`
    """

    def __init__(self, service, uri):
        # not calling parents __init__ #pylint: disable=W0231
        assert urisplit(uri)[3:] == (None, None), "Invalid URI <%s>" % uri

        self.service = service
        self.uri = uri
        self.metadata = Graph(service.store, URIRef(uri+"#metadata"))
        self._graph = Graph(service.store, uri)
        if __debug__:
            self._readonly_graph = ReadOnlyGraph(self._graph)

    def __str__(self):
        return "<%s>" % self.uri

    #
    # .interface.Resource implementation
    #

    def factory(self, uri, _rdf_type=None, _no_spawn=False):
        """I implement :meth:`.interface.ICore.factory`.
        """
        # while it is not technically an error to violate the assertion below
        # (factory should simply return None in that case)
        # this is usually a design error, and rdfrest.cores.factory.factory should
        # be used instead
        assert uri.startswith(self.service.root_uri), uri

        # we do not use rdfrest.get_wrapped
        # (see comment at the top of the file for explanations)
        return self.service.get(coerce_to_uri(uri), _rdf_type, _no_spawn)

    def get_state(self, parameters=None):
        """I implement :meth:`.interface.ICore.get_state`.

        I will first invoke :meth:`check_parameters`.

        The returned graph may have an attribute `redirected_to`, which is
        used to inform :mod:`http_server` that it should perform a redirection.
        """
        self.check_parameters(parameters, "get_state")
        if __debug__:
            return self._readonly_graph
        else:
            return self._graph

    def force_state_refresh(self, parameters=None):
        """I implement :meth:`.interface.ICore.force_state_refresh`.

        I will first invoke :meth:`check_parameters`.
        """
        self.check_parameters(parameters, "force_state_refresh")
        # nothing to do, there is no cache involved

    def edit(self, parameters=None, clear=False, _trust=False):
        """I implement :meth:`.interface.ICore.edit`.

        By default, I do not support it.
        See :class:`EditableCore` to add support.
        """
        raise MethodNotAllowedError("resource is read-only")

    def post_graph(self, graph, parameters=None,
                   _trust=False, _created=None, _rdf_type=None):
        """I implement :meth:`interface.ICore.post_graph`.

        By default, I do not support it.
        See :class:`GraphPostableMixin` to add support.
        """
        raise MethodNotAllowedError("post_graph not supported")

    def delete(self, parameters=None, _trust=False):
        """I implement :meth:`interface.ICore.delete`.

        By default, I do not support it.
        See :class:`EditableCore` to add support.
        """
        raise MethodNotAllowedError("delete not supported")

    #
    # ILocalCore implementation
    #

    def check_parameters(self, parameters, method):
        """I implement :meth:`ILocalCore.check_parameters`.

        I accepts no parameter (not even an empty query string).
        """
        # self is not used #pylint: disable=R0201
        # argument 'method' is not used #pylint: disable=W0613
        if parameters is not None:
            if parameters:
                raise InvalidParametersError("Unsupported parameter(s):" +
                                             ", ".join(parameters.keys()))
            else:
                raise InvalidParametersError("Unsupported parameters "
                                             "(empty dict instead of None)")


    @classmethod
    def complete_new_graph(cls, service, uri, parameters, new_graph,
                           resource=None):
        """I implement :meth:`ILocalCore.complete_new_graph`.

        I leave the graph unchanged.
        """
        pass

    @classmethod
    def check_new_graph(cls, service, uri, parameters, new_graph,
                        resource=None, added=None, removed=None):
        """I implement :meth:`ILocalCore.check_new_graph`.

        I accept any graph.
        """
        # unused arguments #pylint: disable=W0613
        return Diagnosis("check_new_graph")

    @classmethod
    def mint_uri(cls, target, new_graph, created, basename=None, suffix=""):
        """I implement :meth:`ILocalCore.mint_uri`.

        I generate a child URI of `target`'s uri, with a name derived from
        the basename (defaulting to the class name converted to lower case),
        ensuring that the generated URI is not in use in `target.graph`.
        """
        # unsused argument 'created' #pylint: disable=W0613
        target_uri = target.uri
        if target_uri[-1] != "/":
            target_uri += "/"
        if basename is None:
            basename = cls.__name__.lower()
        prefix = "%s%s-" % (target_uri, basename)
        return make_fresh_uri(target.get_state(), prefix, suffix)

    @classmethod
    def create(cls, service, uri, new_graph):
        """I implement :meth:`ILocalCore.create`.

        I store `new_graph` as is in this resource's graph, and adds a hint to
        this class in the metadata graph.
        """
        assert isinstance(uri, URIRef)
        metadata = Graph(service.store, URIRef(uri + "#metadata"))
        metadata.add((uri, NS.hasImplementation, cls.RDF_MAIN_TYPE))

        graph_add = Graph(service.store, uri).add
        for triple in new_graph:
            graph_add(triple)

    RDF_MAIN_TYPE = RDFS.Resource


class EditableCore(LocalCore):
    """I implement `edit` and `delete` from :class:`.interface.ICore`.

    In addition to the helper and hook methods defined by
    :class:`ILocalCore`, this class defines a few others that are
    specific to :meth:`edit` and :meth:`delete`.
    """

    def __init__(self, service, uri):
        LocalCore.__init__(self, service, uri)
        self._edit_context = None

    #
    # .interface.Resource implementation
    #

    def edit(self, parameters=None, clear=False, _trust=False):
        """I implement :meth:`.interface.ICore.edit`.

        On entering the context, I will invoke :meth:`check_parameters`,
        then I will invoke :meth:`prepare_edit`.

        I will
        also raise a `ValueError`:class: if an inner context uses not-None
        parameters that are different from the parameters of the outer context.

        On exiting an untrusted edit context, I will invoke
        :meth:`complete_new_graph` and then :meth:`check_new_graph`, and raise
        an :class:`InvalidDataError` if the later returns an error. Finally,
        :meth:`ack_edit` will be invoked.

        On existing a trusted edit context, only :meth:`ack_edit` will be
        invoked, as the modifications are supposed to be acceptable.

        Several *trusted* contexts can be embeded,
        provided that the inner context use either the exact same parameters as
        the outermost context or no parameter at all (None).
        In that case,
        :meth:`prepare_edit` and :meth:`ack_edit` will only be called
        in the outermost context.

        Note also that :meth:`ack_edit` can itself open a trusted edit context
        if it needs to modify the resource's state.

        .. note::
        
            On exiting a trusted edit context, :meth:`check_new_graph` is
            nonetheless `assert`\ ed, so implementors may notice that, if they
            mistakenly make an invalid modification in a trusted edit context,
            this will be detected and raise an AssertionError.

            This should however not be relied upon, for the following reasons:

            * assertions only occur in `__debug__` mode, not in optimize mode;

            * *not all* tests will be performed by the assertions (see more
              detail in the commented source).

        """
        self.check_parameters(parameters, "edit")
        if parameters is not None:
            parameters = parameters.copy()
            # protects us agains changes to 'parameters' inside 'with' statement
        if _trust:
            assert not clear # not meant to work in a trusted edit context
            return self._edit_trusted(parameters)
        else:
            return self._edit_untrusted(parameters, clear)

    def delete(self, parameters=None, _trust=False):
        """I implement :meth:`.interface.ICore.delete`.

        I will first invoke :meth:`check_parameters`. I will then invoke
        :meth:`check_deletable` to check whether this resource can be deleted.
        If so, I will empty its graph and its metadata graph, then call
        :meth:`ack_delete`.

        After calling this method, the resource object is unsusable and should
        be *immediatetly discarded*.
        """
        self.check_parameters(parameters, "delete")
        diag = self.check_deletable(parameters)
        if not diag:
            raise CanNotProceedError(unicode(diag))
        self.ack_delete(parameters)
        self._graph.remove((None, None, None))
        self.metadata.remove((None, None, None))
        _mark_as_deleted(self)

    #
    # ILocalCore implementation
    #

    def prepare_edit(self, parameters):
        """I implement :meth:`.ILocalCore.prepare_edit`.

        The default implementation returns an empty object.
        """
        # self not used    #pylint: disable=R0201
        # unused arguments #pylint: disable=W0613
        return _Plain()

    def ack_edit(self, parameters, prepared):
        """I implement :meth:`.ILocalCore.ack_edit`.

        The default implementation does nothing.
        """
        pass

    def check_deletable(self, parameters):
        """I implement :meth:`.ILocalCore.check_deletable`.

        The default always accepts.
        """
        # unused self #pylint: disable=R0201
        # unused arguments #pylint: disable=W0613
        return Diagnosis("check_deletable")

    def ack_delete(self, parameters):
        """I implement :meth:`.ILocalCore.ack_delete`.

        The default implementation does nothing.
        """
        # unused arguments #pylint: disable=W0613
        pass

    #
    # private methods
    #

    @contextmanager
    def _edit_trusted(self, parameters):
        """I implement :meth:`edit` in the case it is trusted.
        """
        prepared = None
        if self._edit_context:
            if not self._edit_context[0]:
                raise RdfRestException("Can not embed edit context in an "
                                       "untrusted one")
            ctx_param = self._edit_context[1]
            if parameters is not None  and  parameters != ctx_param:
                raise RdfRestException("Can not embed edit contexts with "
                                       "different parameters")
            outermost = False
        else:
            outermost = True
            self._edit_context = (True, parameters)
            prepared = self.prepare_edit(parameters)

        with self.service:
            try:
                yield self._graph

                # graph is trusted so it SHOULD verify asserts below
                # NB: in the call to check_new_graph below, we force
                # 'added' and 'removed' to empy graphs to save the time
                # of computing them; indeed, they *will* be empty anyway
                # since 'new_graph' is 'self._graph'.
                # As a side effect, all tests that inspect 'added' and
                # 'removed' rather than 'new_graph' will *not* be performed
                # -- but again, this is only an assert for debug purposes,
                # so this is deemed acceptable.
                #
                # Actually, WithReservedNamespacesMixin *relies* on this
                # side effect; indeed, modifications done in a trusted edit
                # context should be allowed to use reserved URIs; it happens
                # that the constraints are checked against 'added' and
                # 'removed' so they are not enforced on trusted edit
                # contexts.
                assert self.check_new_graph(self.service, self.uri, parameters,
                                            self._graph, self,
                                            Graph(), Graph()), \
                       self.check_new_graph(self.service, self.uri, parameters,
                                            self._graph, self,
                                            Graph(), Graph())
                if outermost:
                    self.ack_edit(parameters, prepared)
            finally:
                if outermost:
                    self._edit_context = None

    @contextmanager
    def _edit_untrusted(self, parameters, clear):
        """I implement :meth:`edit` in the case it is untrusted.
        """
        if self._edit_context:
            raise RdfRestException("Can not embed untrusted edit context")
        self._edit_context = (False, parameters)
        prepared = self.prepare_edit(parameters)
        editable = Graph(identifier=self.uri)
        if not clear:
            editable_add = editable.add
            for triple in self._graph: 
                editable_add(triple)

        with self.service:
            try:
                yield editable
                self.complete_new_graph(self.service, self.uri, parameters,
                                        editable, self)
                diag = self.check_new_graph(self.service, self.uri, parameters,
                                            editable, self)
                if not diag:
                    raise InvalidDataError(unicode(diag))

                # we replace self._graph by editable
                # We assume that
                # * most triples between the two graphs are the same
                # * testing that a graph contains a triple is less
                #   costly than adding it or removing it (which involves
                #   updating several indexes -- this is verified by
                #   IOMemory, and roughly so by Sleepycat)
                # so the following should more efficient than simply
                # emptying self_graph and then filling it with
                # editable_graph
                g_add = self._graph.add
                g_remove = self._graph.remove
                g_contains = self._graph.__contains__
                e_contains = editable.__contains__
                for triple in self._graph:
                    if not e_contains(triple):
                        g_remove(triple)
                for triple in editable:
                    if not g_contains(triple):
                        g_add(triple)
                # alter _edit_context so that ack_edit can embed an edit ctxt:
                self._edit_context = (True, parameters)
                self.ack_edit(parameters, prepared)
            finally:
                self._edit_context = None



def compute_added_and_removed(new_graph, old_graph, added=None, removed=None):
    """I compute the graphs of added triples and of removed triples.

    For overridden versions of `check_new_graph` that require `added` and
    `removed` to be set, I should be called as::

        added, removed = self._compute_added_and_removed(
            new_graph, old_graph, added, removed)

    If `added` and `removed` are not None, this method will simply return
    them, preventing the overhead of computing them again.

    However, it is important to call this function *before* the call to
    ``super(...).check_new_graph``, because the result is not transmitted
    to the calling function. So to ensure that the computation happens only
    once, it must be performed at the highest level that needs it.
    """
    if added is None:
        assert removed is None
        _, added, removed = graph_diff(new_graph, old_graph)
    else:
        assert removed is not None
    return added, removed


################################################################
#
# Private functions and classes
#

class _DeletedCore(ICore):
    """
    A deleted RDF-REST core that is not usable anymore.
    """

    _stack = None

    @property
    def _message(self):
        """I compute the exception message, whether _stack is availble or not.
        """
        msg = "This resource has been deleted"
        if self._stack:
            msg += " at:\n" + traceback.format_list(self._stack[-1:])
        return msg
    
    @property
    def uri(self):
        """I implement `interface.ICore.uri`.
        """
        raise TypeError(self._message)

    def factory(self, uri, _rdf_type=None, _no_spawn=False):
        """I implement `interface.ICore.factory`.
        """
        raise TypeError(self._message)

    def get_state(self, parameters=None):
        """I implement `interface.ICore.get_state`.
        """
        raise TypeError(self._message)

    def force_state_refresh(self, parameters=None):
        """I implement `interface.ICore.force_state_refresh`.
        """
        raise TypeError(self._message)

    def edit(self, parameters=None, clear=False, _trust=False):
        """I implement `interface.ICore.edit`.
        """
        raise TypeError(self._message)

    def post_graph(self, graph, parameters=None,
                   _trust=False, _create=None, _rdf_type=None):
        """I implement `interface.ICore.post_graph`.
        """
        raise TypeError(self._message)

    def delete(self, parameters=None, _trust=False):
        """I implement `interface.ICore.delete`.
        """
        raise TypeError(self._message)


def _mark_as_deleted(resource):
    """I mark a resource as deleted.

    The effect is that it attributes will be cleared, and all methods from `the
    uniform interface <rdfrest.interface>`:module: will raise an exception.

    If `__debug__` is set, I will further memorize the stack when this method
    was called, so that debugging is made easier.
    """
    srvc_rsrc_cache = resource.service._resource_cache #pylint: disable=W0212
    del srvc_rsrc_cache[resource.uri]
    
    resource.__dict__.clear()
    resource.__class__ = _DeletedCore
    if __debug__:
        resource._stack = traceback.extract_stack()[:-1]

class _Plain(object):
    """A plain object that can receive arbibtrary attributes."""
    # too few public methods (0/2) #pylint: disable=R0903
    pass
