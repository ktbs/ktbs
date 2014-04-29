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
I provide the implementation of ktbs:Base .
"""
from rdflib import RDF
from contextlib import contextmanager
from threading import current_thread
import posix_ipc

from .resource import KtbsPostableMixin, KtbsResource
from ..api.base import BaseMixin, InBaseMixin
from ..namespace import KTBS, KTBS_NS_URI
from rdfrest.local import _mark_as_deleted


LOCK_DEFAULT_TIMEOUT = 60  # how many seconds to wait for acquiring a lock on the base


class Base(BaseMixin, KtbsPostableMixin, KtbsResource):
    """I provide the implementation of ktbs:Base .
    """
    ######## ILocalResource (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.Base

    RDF_CREATABLE_IN = [ KTBS.hasBase, ]

    def __init__(self, service, uri):
        super(Base, self).__init__(service, uri)
        self.locking_thread_id = None

    def _get_semaphore(self):
        """Return the semaphore for this Base.

        Opens the semaphore if it already exists (keeping its value to what it is),
        or create it with an initial value of 1 if it doesn't exist.

        :return: semaphore for this Base.
        :rtype: posix_ipc.Semaphore
        """
        semaphore = posix_ipc.Semaphore(name=self._get_semaphore_name(),
                                        flags=posix_ipc.O_CREAT,
                                        initial_value=1)
        return semaphore

    def _get_semaphore_name(self):
        """Return this Base semaphore name.

        :return: semaphore name
        :rtype: str
        """
        return str('/' + self.uri.replace('/', '-'))

    @contextmanager
    def lock(self, resource, timeout=None):
        """Lock the current base with a semaphore.

        :param resource: the resource that asks to lock the base.
        :param timeout: maximum time to wait on acquire() until a BusyError is raised.
        :type timeout: int or float
        :raise TypeError: if `resource` no longer exists.
        :raise posix_ipc.BusyError: if we fail to acquire the semaphore until timeout.
        """
        # Make sure the resource still exists (it could have deleted by a concurrent process).
        if not len(resource.state) > 0:
            resource_label = resource.get_label()
            _mark_as_deleted(resource)
            raise TypeError('The resource <{label}> no longer exists.'.format(label=resource_label))

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
                thread_id = getattr(self, 'locking_thread_id', 'unknown')
                error_msg = 'The base <{base_uri}> is locked by thread {thread_id}.'.format(base_uri=self.uri,
                                                                                            thread_id=thread_id)
                raise posix_ipc.BusyError(error_msg)

    def delete(self, parameters=None, _trust=False):
        """I override :meth:`rdfrest.local.EditableResource.delete`.
        """
        with self.lock(self):
            super(Base, self).delete(parameters, _trust)

    @contextmanager
    def edit(self, parameters=None, clear=False, _trust=False):
        """I override :meth:`rdfrest.local.EditableResource.edit`.
        """
        with self.lock(self), super(Base, self).edit(parameters, clear, _trust) as editable:
            yield editable

    def post_graph(self, graph, parameters=None,
                   _trust=False, _created=None, _rdf_type=None):
        """I override :meth:`rdfrest.mixins.GraphPostableMixin.post_graph`.
        """
        with self.lock(self):
            return super(Base, self).post_graph(graph, parameters,
                                                _trust, _created, _rdf_type)

    def ack_delete(self, parameters):
        """I override :meth:`rdfrest.util.EditableResource.ack_delete`.
        """
        super(Base, self).ack_delete(parameters)
        root = self.get_root()
        with root.edit(_trust=True) as editable:
            editable.remove((root.uri, KTBS.hasBase, self.uri))
            editable.remove((self.uri, RDF.type, self.RDF_MAIN_TYPE))
        self._get_semaphore().unlink()  # remove the semaphore from this Base as it no longer exists

    def ack_post(self, parameters, created, new_graph):
        """I override :meth:`rdfrest.util.GraphPostableMixin.ack_post`.
        """
        super(Base, self).ack_post(parameters, created, new_graph)
        with self.edit(_trust=True) as editable:
            editable.add((self.uri, KTBS.contains, created))
            for typ in new_graph.objects(created, RDF.type):
                if typ.startswith(KTBS_NS_URI):
                    assert typ in (KTBS.TraceModel, KTBS.Method,
                                   KTBS.StoredTrace, KTBS.ComputedTrace)
                    editable.add((created, RDF.type, typ))
                    break
            else: # no valid rdf:type was found; should not happen
                assert 0, "No valid rdf:type was found for posted resource"

    def check_deletable(self, parameters):
        """I override :meth:`rdfrest.util.EditableResource.check_deletable`.

        Only an empty base can be deleted.
        """
        diag = super(Base, self).check_deletable(parameters)
        if self.state.value(self.uri, KTBS.contains):
            diag.append("Can not delete non-empty Base")
        return diag

    def find_created(self, new_graph):
        """I override :meth:`rdfrest.util.GraphPostableMixin.find_created`.

        I look for the ktbs:contains property, pointing to something a base
        can contain.
        """
        query = """PREFIX ktbs: <%s>
                   SELECT DISTINCT ?c
                   WHERE { <%s> ktbs:contains ?c .
                           { ?c a ktbs:TraceModel } UNION
                           { ?c a ktbs:Method } UNION
                           { ?c a ktbs:StoredTrace } UNION
                           { ?c a ktbs:ComputedTrace }
                         }
        """ % (KTBS, self.uri)
        return self._find_created_default(new_graph, query)


class InBase(InBaseMixin, KtbsResource):
    """I provide common implementation of all elements contained in a base.
    """
    ######## ILocalResource (and mixins) implementation  ########

    RDF_CREATABLE_IN = [ KTBS.contains, ]

    def ack_delete(self, parameters):
        """I override :meth:`rdfrest.util.DeletableMixin.ack_delete`.
        """
        super(InBase, self).ack_delete(parameters)
        base = self.get_base()
        with base.edit(_trust=True) as editable:
            editable.remove((base.uri, KTBS.contains, self.uri))
            editable.remove((self.uri, RDF.type, self.RDF_MAIN_TYPE))

    def delete(self, parameters=None, _trust=False):
        """I override :meth:`rdfrest.local.EditableResource.delete`.
        """
        base = self.get_base()
        with base.lock(self):
            super(InBase, self).delete(parameters, _trust)

    @contextmanager
    def edit(self, parameters=None, clear=False, _trust=False):
        """I override :meth:`rdfrest.local.EditableResource.edit`.
        """
        base = self.get_base()
        with base.lock(self), super(InBase, self).edit(parameters, clear, _trust) as editable:
            yield editable
