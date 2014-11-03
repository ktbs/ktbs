# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
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
from rdfrest.cores import ICore
from rdfrest.util import cache_result
from urlparse import unquote

from ..utils import extend_api_ignore, extend_api, short_name, SKOS

@extend_api
class KtbsResourceMixin(ICore):
    """
    I provide the pythonic interface common to all kTBS resources.
    """

    ######## Abstract kTBS API ########

    def get_id(self):
        """
        Return the identifier of this resource.
        """
        return short_name(self.uri)

    @extend_api_ignore
    def get_uri(self):
        """
        Return the URI of this resource.
        """
        return self.uri
        # this method is defined for the sole purpose of complying with the
        # abstract API, as 'uri' is already available as an attribute;
        #
        # the decorator extend_api_ignore above prevents extend_api to create
        # a recursive loop by making a 'uri' prop using this method...

    def get_label(self):
        """
        Return a user-friendly label for this resource.

        If no label has been set, a default label is generated from this
        resource's URI.
        """
        pref_label = self.state.value(self.uri, SKOS.prefLabel)
        if pref_label is not None:
            return unicode(pref_label)

        label = self.state.value(self.uri, RDFS.label)
        if label is not None:
            return unicode(label)

        ret = short_name(self.uri)
        if ret[-1] == "/":
            ret = ret[:-1]
        if ret[0] == "#":
            ret = ret[1:]
        ret = unquote(ret)
        ret = ret.replace("_", " ")
        return ret

    def set_label(self, value):
        """
        Set a user-friendly label for this resource.
        """
        with self.edit() as graph:
            graph.set((self.uri, SKOS.prefLabel, Literal(value)))

    def reset_label(self):
        """
        Reset the user-friendly label to its default value.
        """
        with self.edit() as graph:
            graph.remove((self.uri, SKOS.prefLabel, None))
            graph.remove((self.uri, RDFS.label, None))

    def remove(self):
        """
        Remove this resource from the kTBS.
        """
        self.delete()

    def get_readonly(self):
        """I return True if this resource can not be modified
        """
        return self and False #used self to lure pylint
        # TODO LATER find a good way to know if this resource is readonly

    def get_sync_status(self):
        """I return True if this resource is up to date

        This is meaningful only if the resource is a "view" on a remote
        resource. If the resource is self-contained, it is always up to date.
        """
        return self and False #used self to lure pylint
        # TODO LATER find a good way to know if this resource is synced

    ######## Extension to the abstract kTBS API ########

    @property
    @cache_result
    def state(self):
        """I store and return the result of `get_state`.

        This property makes it more concise and hopefully slightly more
        efficient than to call :meth:`rdfrest.cores.ICore.get_state`
        each time we need this resource's graph.

        Note that this graph must not be edited. We must use
        :meth:`rdfrest.cores.ICore.get_state` instead.
        """
        return self.get_state()

