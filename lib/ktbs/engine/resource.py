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
from rdfrest.local import EditableResource
from rdfrest.mixins import BookkeepingMixin, FolderishMixin, \
    GraphPostableMixin, WithCardinalityMixin, WithReservedNamespacesMixin, \
    WithTypedPropertiesMixin
from re import compile as RegExp, UNICODE
from contextlib import contextmanager
from threading import current_thread
import posix_ipc

from ..api.resource import KtbsResourceMixin
from ..namespace import KTBS
from ..utils import mint_uri_from_label, SKOS

METADATA = Namespace("tag:silex.liris.cnrs.fr.2012.08.06.ktbs.metadata:")

# TODO take this variable from the global kTBS conf file
LOCK_DEFAULT_TIMEOUT = 60  # how many seconds to wait for acquiring a lock on the base


class KtbsResource(KtbsResourceMixin, WithCardinalityMixin,
                   WithReservedNamespacesMixin, WithTypedPropertiesMixin,
                   BookkeepingMixin, EditableResource):
    """I provide common methods and class parameters for all KTBS Resources.

    Especially, I include a number of of required other mixins.
    """
    ######## ILocalResource (and mixins) implementation  ########

    RDF_RESERVED_NS = [KTBS]

    def __init__(self, service, uri):
        super(KtbsResource, self).__init__(service, uri)
        self.locking_thread_id = None

    @classmethod
    def mint_uri(cls, target, new_graph, created, basename=None, suffix=""):
        """I override :meth:`rdfrest.local.ILocalResource.mint_uri`.

        I use the skos:prefLabel of the resource to mint a URI, else the
        basename (if provided), else the class name.
        """
        label = (new_graph.value(created, SKOS.prefLabel)
                 or basename
                 or cls.__name__)
        return mint_uri_from_label(label, target, suffix=suffix)

    @contextmanager
    def lock(self, timeout=None):
        # Set the timeout for acquiring the semaphore.
        if timeout is None:
            timeout = LOCK_DEFAULT_TIMEOUT

        # If the current thread wants to access the base he is good to go.
        # This should only happen when the thread wants to lock the base further down the call stack.
        if self.locking_thread_id == current_thread().ident:
            yield

        # Else, either another thread wants to access the base (and he will wait until the lock is released),
        # or the current thread wants to access the base and it is not locked yet.
        else:
            semaphore = self._get_semaphore()

            try:  # acquire the lock, re-raise BusyError with info if it fails
                semaphore.acquire(timeout)
                self.locking_thread_id = current_thread().ident

                try:  # catch exceptions occurring after the lock has been acquired
                    yield
                finally:  # make sure we exit properly by releasing the lock
                    self.locking_thread_id = None
                    semaphore.release()
                    semaphore.close()

            except posix_ipc.BusyError:
                thread_id = self.locking_thread_id if self.locking_thread_id else 'Unknown'
                error_msg = 'The resource <{res_uri}> is locked by thread {thread_id}.'.format(res_uri=self.uri,
                                                                                               thread_id=thread_id)
                raise posix_ipc.BusyError(error_msg)

    def _get_semaphore(self):
        return posix_ipc.Semaphore(name=self._get_semaphore_name(),
                                   flags=posix_ipc.O_CREAT,
                                   initial_value=1)

    def _get_semaphore_name(self):
        raise NotImplementedError

class KtbsPostableMixin(FolderishMixin, GraphPostableMixin, KtbsResource):
    """I implement the common post-related functionalities for KtbsResources.
    """

    def check_posted_graph(self, parameters, created, new_graph):
        """I implement
        :meth:`rdfrest.local.GraphPostableMixin.check_posted_graph`.
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

