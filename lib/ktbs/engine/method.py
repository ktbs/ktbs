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
I provide the implementation of ktbs:Method .
"""
from logging import getLogger

from rdflib import Literal, URIRef

from rdfrest.cores.local import compute_added_and_removed
from rdfrest.util import parent_uri
from .base import InBase
from .builtin_method import get_builtin_method_impl
from ..api.method import MethodMixin
from ..namespace import KTBS


LOG = getLogger(__name__)


class Method(MethodMixin, InBase):
    """I provide the implementation of ktbs:Method .
    """
    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.Method

    RDF_EDITABLE_OUT =    [ KTBS.hasParentMethod,
                            KTBS.hasParameter,
                            ]
    RDF_CARDINALITY_OUT = [ (KTBS.hasParentMethod, 1, 1),
                            ]
    RDF_TYPED_PROP =      [ (KTBS.hasParentMethod, "uri"),
                            (KTBS.hasParameter,    "literal"),
                            ]

    @classmethod
    def create(cls, service, uri, new_graph):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.create`
        """
        super(Method, cls).create(service, uri, new_graph)
        parent_method_uri = new_graph.value(uri, KTBS.hasParentMethod)
        my_base = parent_uri(uri)
        parent_base = parent_uri(parent_method_uri)
        if my_base == parent_base: # parent is not a built-in method
            parent = service.get(parent_method_uri)
            with parent.edit(_trust=True) as editable:
                editable.add((uri, KTBS.hasParentMethod, parent_method_uri))

    @classmethod
    def complete_new_graph(cls, service, uri, parameters, new_graph,
                           resource=None):
        """I implement :meth:`ILocalCore.complete_new_graph`.

        I handle the deprecated property ktbs:inherits, replacing it with
        ktbs:hasParentMethod
        """
        # TODO LATER remove this, as this is a deprecated feature
        uses_inherits = False
        if resource is None:
            for inherited in new_graph.objects(uri, cls._INHERITS):
                new_graph.add((uri, KTBS.hasParentMethod, inherited))
                uses_inherits = True
        else:
            added, removed = compute_added_and_removed(new_graph,
                                                       resource.state,
                                                       None, None)
            for added_parent in added.objects(uri, cls._INHERITS):
                new_graph.add((uri, KTBS.hasParentMethod, added_parent))
                uses_inherits = True
            for rem_parent in removed.objects(uri, cls._INHERITS):
                new_graph.remove((uri, KTBS.hasParentMethod, rem_parent))
                uses_inherits = True
        if uses_inherits:
            LOG.warn("Use of deprecated property ktbs:inherits")
        # end deprecated

    @classmethod
    def check_new_graph(cls, service, uri, parameters, new_graph,
                        resource=None, added=None, removed=None):
        """I overrides :meth:`rdfrest.cores.local.ILocalCore.check_new_graph`

        I check that parent and parameters are acceptable
        """
        if resource is None:
            the_graph = new_graph
        else:
            old_graph = resource.state
            added, removed = compute_added_and_removed(new_graph, old_graph,
                                                       added, removed)
            the_graph = added # we only check values that were added/changed
            
        diag = super(Method, cls).check_new_graph(
            service, uri, parameters, new_graph, resource, added, removed)
        
        # check parent method (if it has been changed)
        parent_method_uri = the_graph.value(uri, KTBS.hasParentMethod)
        if parent_method_uri is not None:
            my_base = parent_uri(uri)
            parent_base = parent_uri(parent_method_uri)
            if my_base == parent_base:
                parent = service.get(URIRef(parent_method_uri))
                if parent is None:
                    diag.append("Parent method does not exist <%s>"
                                % parent_method_uri)
                elif parent.RDF_MAIN_TYPE != KTBS.Method:
                    diag.append("Parent <%s> is not a method"
                                % parent_method_uri)
            else:
                if not get_builtin_method_impl(parent_method_uri):
                    diag.append("Parent method is neither in same base nor "
                                "built-in <%s>" % parent_method_uri)

        # check new parameters
        new_params = False
        for param in the_graph.objects(uri, KTBS.hasParameter):
            new_params = True
            if not isinstance(param, Literal):
                diag.append("Parameters should be literals; "
                              "got <%s>" % param)
            if "=" not in param:
                diag.append("Parameter is ill-formatted: %r" % str(Literal))

        # check global integrity of parameters (including unchanged ones)
        if new_params:
            seen = set()
            for param in new_graph.objects(uri, KTBS.hasParameter):
                key, _ = param.split("=", 1)
                if key in seen:
                    diag.append("Parameter %s specified more than once" % key)
                else:
                    seen.add(key)

        return diag

    def prepare_edit(self, parameters):
        """I overrides :meth:`rdfrest.cores.local.ILocalCore.prepare_edit`

        I store old values of some properties (parent, parameters)
        to handle the change in :meth:`ack_edit`.
        """
        ret = super(Method, self).prepare_edit(parameters)
        ret.old_parent = self.state.value(self.uri, KTBS.hasParentMethod)
        ret.old_params = set(self.state.objects(self.uri, KTBS.hasParameter))
        return ret

    def ack_edit(self, parameters, prepared):
        """I overrides :meth:`rdfrest.cores.local.ILocalCore.ack_edit`

        I reflect changes in the related resources (parent method)
        """
        super(Method, self).ack_edit(parameters, prepared)
        new_parent = self.state.value(self.uri, KTBS.hasParentMethod)
        if prepared.old_parent != new_parent:
            self._ack_parent_change(prepared.old_parent, new_parent)
        new_params = set(self.state.objects(self.uri, KTBS.hasParameter))
        if prepared.old_params != new_params:
            self._ack_parameter_change()
    
    def ack_delete(self, parameters):
        """I overrides :meth:`rdfrest.cores.local.ILocalCore.ack_delete`
        """
        parent_method_uri = self.state.value(self.uri, KTBS.hasParentMethod)
        self._ack_parent_change(parent_method_uri, None)
        super(Method, self).ack_delete(parameters)

    def check_deletable(self, parameters):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.check_deletable`

        I refuse to be deleted if I am used by a trace.
        """
        diag = super(Method, self).check_deletable(parameters)
        for i in self.state.subjects(KTBS.hasMethod, self.uri):
            diag.append("<%s> is used (ktbs:hasMethod) by <%s>"
                        % (self.uri, i))
        for i in self.state.subjects(KTBS.hasParentMethod, self.uri):
            diag.append("<%s> is used (ktbs:hasParentMethod) by <%s>"
                        % (self.uri, i))
        return diag

    # TODO LATER remove this, as this is a deprecated feature
    _INHERITS = URIRef("%sinherits" % KTBS)
    RDF_EDITABLE_OUT += [ _INHERITS, ]

    ######## Private methods ########

    def _ack_parameter_change(self):
        """Called whenever a parameter or parent changes.
        """
        for trace in self.iter_used_by():
            trace._mark_dirty() # friend #pylint: disable=W0212
        for child in self.iter_children():
            child._ack_parameter_change() # friend #pylint: disable=W0212

    def _ack_parent_change(self, old_parent_uri, new_parent_uri):
        """Called whenever a parameter or parent changes.
        """
        old_parent = self.service.get(old_parent_uri)
        if old_parent is not None: # it is not a built-in method
            with old_parent.edit(_trust=True) as editable:
                editable.remove((
                        self.uri, KTBS.hasParentMethod, old_parent_uri))
        if new_parent_uri is not None:
            new_parent = self.service.get(new_parent_uri)
            if new_parent is not None: # it is not a built-in method
                with new_parent.edit(_trust=True) as editable:
                    editable.add((
                            self.uri, KTBS.hasParentMethod, new_parent_uri))
        self._ack_parameter_change()
