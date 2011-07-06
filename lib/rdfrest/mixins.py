#    This file is part of RDF-REST <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
I provide useful mixin classes to enhance `rdflib.resource.Resource`.

Note that mixins providing HTTP verbs (RdfGetMixin, RdfPutMixin, RdfPostMixin
and DeleteMixin) should in general appear *after* mixins altering their
behaviour (whose names are starting with *With*).

This is due to the fact tha "With" mixins do not inherit "HTTP" mixins: they do 
not strongly depend on them, they only alter their functionality *if* present.
"""
from datetime import datetime
from itertools import chain
from md5 import md5
from rdflib import BNode, Literal, RDF, URIRef
from rdflib.compare import graph_diff
from StringIO import StringIO
from webob import Response
from .iso8601 import parse_date
from .namespaces import RDFREST, DC
from .parser import parse
from .resource import Resource
from .utils import cache_result


class RdfGetMixin(Resource):
    """
    I implement a straightforward GET method.

    The GET method simply serializes this resource's RDF description.
    """

    def http_get(self, request):
        """
        Serialize this resource RDF description.
        """
        res = Response(request=request)
        self.negociate_rdf_content(res, self.graph)
        return res


class RdfPutMixin(Resource):
    """
    I implement a PUT method.
    The PUT method accept an RDF graph (in any understandable syntax),
    checks whether the new graph is acceptable,
    then replace the graph of that resource with it.
    """

    def http_put(self, request):
        """
        Change this resource's public graph.
        """
        # TODO implement a 'diff' format and handle it here
        #new_graph = parse(request.body_file, request.content_type, self.uri)
        # FIXME: the above hangs indefinitely, so we do the hack below:
        # NB: fix it also in RdfPostMixin.http_post
        # begin-hack
        body_file = StringIO(request.body)
        new_graph = parse(body_file, request.content_type, self.uri)
        # end-hack
        if new_graph is None:
            return Response(request=request, status="400 Invalid RDF payload")
        _, removed, added = graph_diff(self.graph, new_graph)
        res = self.check_put(request, new_graph, removed, added)
        if res is None: # then new_graph is acceptable
            self.graph.remove((None, None, None))
            add = self.graph.add
            for triple in new_graph:
                # TODO faster way to do that?
                add(triple)
            res = Response(request=request)
            self.negociate_rdf_content(res, self.graph)
        return res

    def check_put(self, _request, _new_graph, _removed, _added):
        """
        Check whether `new_graph` is acceptable for PUT.

        If acceptable, None is returned; else, a Response with the appropriate
        error status should be returned.

        This method may also alter new_graph if required.

        TODO: describe parameters
        """
        #pylint: disable=R0201
        #    Method could be a function
        return None


class RdfPostMixin(Resource):
    """
    I implement a POST method.

    The POST method accept an RDF graph (in any understandable syntax),
    checks whether it represent an acceptable child resource,
    then create that child resource.
    """

    def http_post(self, request):
        """
        Create a new child resource.
        """
        #new_graph = parse(request.body_file, request.content_type, self.uri)
        # FIXME: the above hangs indefinitely, so we do the hack below:
        # NB: fix it also in RdfPutMixin.http_put
        # begin-hack
        body_file = StringIO(request.body)
        new_graph = parse(body_file, request.content_type, self.uri)
        # end-hack

        if new_graph is None:
            return Response(request=request, status="400 Invalid RDF payload")
        created = self.find_created(request, new_graph)
        if created is None:
            return Response(request=request,
                            status="400 Can not find created node")
        get_class = self.service.class_map.get
        resource_class = None
        for typ in new_graph.objects(created, RDF.type):
            candidate = get_class(typ)
            if candidate is None:
                continue
            if resource_class:
                return Response(request=request,
                                status="400 Ambiguous type of posted resource")
            resource_class = candidate

        if not isinstance(created, URIRef):
            new_uri = resource_class.mint_uri(created, new_graph, self.uri)
            add_triple = new_graph.add
            rem_triple = new_graph.remove
            subst = lambda x: (x == created) and new_uri or x
            for triple in new_graph:
                # heuristics: most triple will involve created, so we replace
                # all of them, even those that will not be changed by subst
                rem_triple(triple)
                add_triple([ subst(i) for i in triple ])
            created = new_uri

        res = self.check_post(request, created, new_graph)
        if res: # new_graph is not acceptable to this resource
            return res

        res = resource_class.check_new_graph(request, created, new_graph)
        if res: # new_graph is not acceptable to the target class
            return res

        posted = resource_class(self.service, created)
        posted.init(new_graph)
        self.ack_posted(posted)

        return Response(request=request, status="201 Created", headerlist=[
                ("location", str(created)),
                ])
 
    def find_created(self, _request, new_graph):
        """
        Find the node represented the resource to be created in `new_graph`.

        If none can be found, return None.

        The default implementation uses the following heuristics to guess the
        created node, but you may wish to override it:

        * if the target URI is linked to a single node, that node is returned
          (unless it is a litteral or a URI with a fragment)
        * if the targer URI is linked to several node, one of them being a URI
          without fragment, and all the others being URIRef of that URI,
          then the URI without fragment is returned
        """
        query_objects = "SELECT ?o WHERE { <%s> ?p ?o }" % self.uri
        query_subjects = "SELECT ?s WHERE { ?s ?p <%s> }" % self.uri
        candidates = set(chain(new_graph.query(query_objects),
                               new_graph.query(query_subjects)))
        candidates = [ cand for cand in candidates
                       if not isinstance(cand, Literal) ]

        if len(candidates) == 1:
            candidate = candidates[0]
            if isinstance(candidate, URIRef) and '#' in candidate:
                #print "===", "only candidate has a fragment %s" % candidate
                return None
            else:
                return candidate

        base_candidates = [ cand for cand in candidates
                            if isinstance(cand, URIRef)
                            and "#" not in cand ]
        if len(base_candidates) != 1:
            #print "===", "not just one candidate %s" % candidates
            return None

        base = base_candidates.pop()
        candidates.remove(base)
        prefix = base+"#"
        for other in candidates:
            if isinstance(other, BNode):
                #print "===", "bnodes + base"
                return None # can not decide between 'base' and blank nodes
            # else its is a URIRef (Literals have been removed before)
            if not other.startswith(prefix):
                #print "===", "other is not a fragment of base"
                return None
        return base # all other candidates are 'fragments' of the base

    def check_post(self, _request, _uri, _new_graph):
        """
        Check whether `new_graph` is acceptable for a POST on this resource.

        If acceptable, None is returned; else, a Response with the appropriate
        error status should be returned.

        This method may also alter new_graph if required.
        """
        #pylint: disable=R0201
        #    Method could be a function
        return None

    def ack_posted(self, posted_resource):
        """
        I am called just after a new resource has been succesfully posted.
        """
        pass

    @classmethod
    def check_new_graph(cls, request, uri, new_graph):
        """
        Postable resources must have a URI ending with a slash.
        """
        if uri[-1] != "/":
            return Response(request=request,
                            status="400 URI should end with '/'")
        return super(RdfPostMixin, cls).check_new_graph(request, uri,
                                                        new_graph)


class DeleteMixin(Resource):
    """
    I implement a DELETE method.

    The DELETE method checks whether this resource can be safely deleted,
    and if so deletes it from the service.
    """

    def http_delete(self, request):
        """
        Delete this resource.
        """
        raise NotImplementedError()


class WithPreconditionMixin(Resource):
    """
    I implement HTTP headers related to pre-condition in GET and PUT.

    HTTP uses last-modified date and etags to express pre-conditions on GET and
    PUT. See section 13.3 of :RFC:`2616` .
    """

    def get_response(self, request):
        """
        I override get_response to intercept GET and PUT methods.

        :see-also: `wrap_get`, `wrap_put`
        """
        method = request.method
        if method == "HEAD" or method == "GET":
            return self.wrap_get(request)
        elif method == "PUT":
            return self.wrap_put(request)
        else:
            return super(WithPreconditionMixin, self).get_response(request)
                                     
    def wrap_get(self, request):
        """
        I make the returned `response` object aware of pre-conditions.
        """
        res = super(WithPreconditionMixin, self).get_response(request)
        res.etag = self.get_etag()
        res.last_modified = self.get_last_modified()
        # TODO: add cache_control based on last_modified
        res.conditional_response = True
        return res

    def wrap_put(self, request):
        """
        I check pre-conditions and fail if they are not matched.

        Note that I do *not* allow a PUT if the resource has an etag and no
        ``IfMatch`` header is provided.
        """
        resource_etag = self.get_etag()
        request_etags = request.if_match
        if str(request_etags) == "*":
            return Response("PUT requests must specify an ETag", status=403)
        match_precondition = request_etags.weak_match(resource_etag)            
        if not match_precondition:
            return  Response("precondition failed", status=412)

        res = super(WithPreconditionMixin, self).get_response(request)
        if res.status[0] == "2": # success
            self.update_metadata()
            if res.status[:3] == "200":
                res.etag = self.get_etag()
                res.last_modified = self.get_last_modified()
        return res

    def get_etag(self):
        """
        Fetch this resource's ETag from the private graph.

        A new etag is created if needed.
        """
        ret = next(self.private.objects(self.uri, _ETAG), None)
        if ret is None:
            ret = Literal(md5(self.uri + _NOW().isoformat()).hexdigest())
            self.private.add((self.uri, _ETAG, ret))
        return ret

    def get_last_modified(self):
        """
        Fetch this resource's LastModified date from the private graph.

        None is returned if no modification date is stored.
        """
        ret = next(self.private.objects(self.uri, _DC_MODIFIED), None)
        if ret is not None:
            ret = parse_date(ret)
        return ret

    def update_metadata(self):
        """
        Update the metadata (etag and last-modified) after a change.

        NB: this method is automatically invoked after a succesful PUT.
        It is provided only to extend the behaviour to other HTTP methods,
        or to initiate a new resource.
        """
        now = _NOW()
        new_etag = md5(self.uri + now.isoformat()).hexdigest()
        self.private.set((self.uri, _ETAG, Literal(new_etag)))
        self.private.set((self.uri, _DC_MODIFIED, Literal(now)))

    def init(self, new_graph):
        """
        I override init to add metadata in the private graph.
        """
        super(WithPreconditionMixin, self).init(new_graph)
        self.update_metadata()


class WithReservedNamespacesMixin(Resource):
    """ 
    I add reserved namespaces to RdfPutMixin and RdfPostMixin.

    A *reserved namespace* is a set of URI (defined by a common prefix) which
    can not be freely used in PUT or POST requests, as they have a specific
    meaning for the application.

    Reserved namespaces are generated by the `iter_reserved_namespaces` class
    method.

    The reserved namespace applies to URIs used as predicates and types.
    The default rule is that they can not be added at POST time (except for
    the *main type* of the resource), and they can not be changed at PUT time.

    It is however possible to provide exceptions for a class, *i.e.* URIs
    inside a reserved namespace which is usable in a given context: POST only,
    or PUT (and POST); incoming property, outgoing property or type. All those
    exceptions are generated by one of the following class method:

    * `iter_postable_types`
    * `iter_postable_in`
    * `iter_postable_out`
    * `iter_puttable_types`
    * `iter_puttable_in`
    * `iter_puttable_out`

    NB: the values yielded by those methods is not supposed to change over
    time, and may therefore be cached.
    """

    @classmethod
    def iter_reserved_namespaces(cls):
        """
        Generate reserved namespaces for this class.
        """
        return ()

    @classmethod
    def iter_postable_types(cls):
        """
        Generate reserved URIs usable as types at POST time. 
        """
        return ()

    @classmethod
    def iter_postable_in(cls):
        """
        Generate reserved URIs usable as incoming properties at POST time. 
        """
        return ()

    @classmethod
    def iter_postable_out(cls):
        """
        Generate reserved URIs usable as outgoing properties at POST time. 
        """
        return ()

    @classmethod
    def iter_puttable_types(cls):
        """
        Generate reserved URIs usable as types at POST/PUT time. 
        """
        return ()

    @classmethod
    def iter_puttable_in(cls):
        """
        Generate reserved URIs usable as incoming properties at POST/PUT time. 
        """
        return ()

    @classmethod
    def iter_puttable_out(cls):
        """
        Generate reserved URIs usable as outgoing properties at POST/PUT time. 
        """
        return ()

    def check_put(self, request, new_graph, removed, added):
        """
        Overrides `rdfrest.mixins.RdfPutMixin.check_put`
        """
        super_check = super(WithReservedNamespacesMixin, self).check_put
        ret = super_check(request, new_graph, removed, added)
        if ret is not None:
            return ret
        triples = chain(removed, added)
        return self.__check_triples(request, triples, "PUT", self.uri)

    @classmethod
    def check_new_graph(cls, request, uri, new_graph):
        """
        Method used by `rdfrest.mixins.RdfPostMixin`
        """
        super_check = super(WithReservedNamespacesMixin, cls).check_new_graph
        ret = super_check(request, uri, new_graph)
        if ret is not None:
            return ret

        return cls.__check_triples(request, new_graph, "POST", uri)

    #
    # private method
    #
    @classmethod
    @cache_result
    def __get_reserved_namespaces(cls):
        """
        Cache the set of all reserved namespaces.
        """
        return frozenset(cls.iter_reserved_namespaces())

    @classmethod
    @cache_result
    def __get_postable_types(cls):
        """
        Cache the set of all postable types.
        """
        return frozenset(chain([cls.MAIN_RDF_TYPE],
                               cls.iter_postable_types(),
                               cls.iter_puttable_types(),
                               ))

    @classmethod
    @cache_result
    def __get_postable_in(cls):
        """
        Cache the set of all postable incoming properties.
        """
        return frozenset(chain(cls.iter_postable_in(),
                               cls.iter_puttable_in(),
                               ))

    @classmethod
    @cache_result
    def __get_postable_out(cls):
        """
        Cache the set of all postable outgoing properties.
        """
        return frozenset(chain(cls.iter_postable_out(),
                               cls.iter_puttable_out(),
                               ))

    @classmethod
    @cache_result
    def __get_puttable_types(cls):
        """
        Cache the set of all puttable types.
        """
        return frozenset(cls.iter_puttable_types())

    @classmethod
    @cache_result
    def __get_puttable_in(cls):
        """
        Cache the set of all puttable incoming properties.
        """
        return frozenset(cls.iter_puttable_in())

    @classmethod
    @cache_result
    def __get_puttable_out(cls):
        """
        Cache the set of all puttable outgoing properties.
        """
        return frozenset(cls.iter_puttable_out())

    @classmethod
    def __check_triples(cls, request, triples, method, uri):
        """
        Check whether a new graph is valid for the given request.

        request
            the request being processed
        triples
            an iterable of triples to be changed (removed or added)
        method
            "POST" or "PUT", extracted from request
        uri
            the URI of the resource being created (POST) or changed (PUT)

        Return None if the triples are OK, or a Response with an error status
        code of there is a problem.
        """

        if method == "POST":
            types = cls.__get_postable_types()
            in_ = cls.__get_postable_in()
            out = cls.__get_postable_out()
        else:
            assert method == "PUT"
            types = cls.__get_puttable_types()
            in_ = cls.__get_puttable_in()
            out = cls.__get_puttable_out()
        reserved = cls.__get_reserved_namespaces()
        def is_reserved(a_uri):
            "determine if uri is reserved"
            for i in reserved:
                if a_uri.startswith(i):
                    return True
            return False

        for s, p, o in triples:
            if s == uri:
                if p == _RDF_TYPE:
                    if is_reserved(o) and o not in types:
                        return Response("Can not %s type <%s> for <%s>"
                                        % (method, o, uri),
                                        "403 Forbidden (reserved type)",
                                        request=request)
                elif is_reserved(p) and p not in out:
                    return Response("Can not %s property <%s> of <%s>"
                                    % (method, p, uri),
                                    "403 Forbidden (reserved out-property)",
                                    request=request)
            elif o == uri:
                if is_reserved(p) and p not in in_:
                    return Response("Can not %s property <%s> to <%s>"
                                    % (method, p, uri),
                                    "403 Forbidden (reserved in-property)",
                                    request=request)

        # NB: cardinality constraints (e.g. required or unique properties)
        # can not trivially be checked in this loop, as it has no knowledge
        # of the old graph (only changes), so we manage them in another
        # plugin.


class WithCardinalityMixin(Resource):
    """
    I add cardinality constrains to RdfPutMixin and RdfPostMixin.

    I provide means to express cardinality constraints on some predicate,
    used as incoming and/or outgoing properties, and override `check_put` and
    `check_new_graph` to enforce those constraints.

    Cardinality constraints are expressed by the following methods, generating
    triples of the form (predicate_uri, min_cardinality, max_cardinality),
    respectively for incoming and outgoing properties. ``None`` can be used
    for min_cardinality or max_cardinality to mean "no constraint".

    * `iter_cardinality_in`
    * `iter_cardinality_out`

    NB: the values yielded by those methods is not supposed to change over
    time, and may therefore be cached.
    """

    @classmethod
    def iter_cardinality_in(cls):
        """
        Generate cardinality constraints for incoming properties.
        """
        return ()

    @classmethod
    def iter_cardinality_out(cls):
        """
        Generate cardinality constraints for outgoing properties.
        """
        return ()

    def check_put(self, request, new_graph, removed, added):
        """
        Overrides `rdfrest.mixins.RdfPutMixin.check_put`
        """
        super_check = super(WithCardinalityMixin, self).check_put
        ret = super_check(request, new_graph, removed, added)
        if ret is not None:
            return ret
        return self.__check_triples(request, new_graph , self.uri)

    @classmethod
    def check_new_graph(cls, request, uri, new_graph):
        """
        Method used by `rdfrest.mixins.RdfPostMixin`
        """
        super_check = super(WithCardinalityMixin, cls).check_new_graph
        ret = super_check(request, uri, new_graph)
        if ret is not None:
            return ret

        return cls.__check_triples(request, new_graph, uri)

    #
    # private method
    #
    @classmethod
    @cache_result
    def __get_cardinality_in(cls):
        """
        Cache the set of cardinality constraints for incoming properties.
        """
        return frozenset(cls.iter_cardinality_in())

    @classmethod
    @cache_result
    def __get_cardinality_out(cls):
        """
        Cache the set of cardinality constraints for outgoing properties.
        """
        return frozenset(cls.iter_cardinality_out())

    @classmethod
    def __check_triples(cls, request, new_graph, uri):
        """
        Check whether a new graph is valid for the given request.

        request
            the request being processed
        new_graph
            the new graph
        uri
            the URI of the resource being created (POST) or changed (PUT)

        Return None if the new_graph is OK, or a Response with an error status
        code of there is a problem.
        """
        new_graph_subjects = new_graph.subjects
        for p, minc, maxc in cls.__get_cardinality_in():
            nbp = len(list(new_graph_subjects(p, uri)))
            if minc is not None and nbp < minc:
                return Response("Property <%s> to <%s> should have at least "
                                "%s subjects; it only has %s"
                                % (p, uri, minc, nbp),
                                "403 Forbidden (minimum in-cardinality)",
                                request=request)
            if maxc is not None and nbp > maxc:
                return Response("Property <%s> to <%s> should have at most "
                                "%s subjects; it has %s"
                                % (p, uri, minc, nbp),
                                "403 Forbidden (maximum in-cardinality)",
                                request=request)

        new_graph_objects = new_graph.objects
        for p, minc, maxc in cls.__get_cardinality_out():
            nbp = len(list(new_graph_objects(uri, p)))
            if minc is not None and nbp < minc:
                return Response("Property <%s> of <%s> should have at least "
                                "%s objects; it only has %s"
                                % (p, uri, minc, nbp),
                                "403 Forbidden (minimum out-cardinality)",
                                request=request)
            if maxc is not None and nbp > maxc:
                return Response("Property <%s> of <%s> should have at most "
                                "%s objects; it has %s"
                                % (p, uri, minc, nbp),
                                "403 Forbidden (maximum out-cardinality)",
                                request=request)


_DC_MODIFIED = DC.modified
_ETAG = RDFREST.etag
_NOW = datetime.utcnow
_RDF_TYPE = RDF.type
