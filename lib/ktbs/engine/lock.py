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
I provide a locking mechanism for resource that needs protection in the context of concurrency.

"""
import posix_ipc
import sys
from md5 import md5

from logging import getLogger
from threading import current_thread
from contextlib import contextmanager

from os import getpid, pathconf

from rdfrest.cores.local import _mark_as_deleted
from rdfrest.cores.local import ILocalCore


LOG = getLogger(__name__)
PID = getpid()

if sys.platform.lower().find('darwin') != -1:
    def get_semaphore_name(resource_uri):
        """Return a safe semaphore name for a resource.

        :param basestring resource_uri: the URI of the resource.
        :return: safe semaphore name.
        :rtype: str
        """

        sem_name = md5(resource_uri).hexdigest()[:29]
        return sem_name
else:
    NAME_MAX_SEM = pathconf("/", 'PC_NAME_MAX') - 4 # according to man 7 sem_overview
    def get_semaphore_name(resource_uri):
        """Return a safe semaphore name for a resource.

        posix_ipc doesn't accept '/' inside the semaphore name but the name must
        begin with '/'.

        :param basestring resource_uri: the URI of the resource.
        :return: safe semaphore name.
        :rtype: str
        """

        sem_name = str('/' + resource_uri.replace('/', '-'))
        if len(sem_name) > NAME_MAX_SEM:
            sem_name = '/' + md5(resource_uri).hexdigest()
        return sem_name


class WithLockMixin(ILocalCore):
    """ I provide methods to lock a resource.

    :cvar int __locking_thread_id: id of the thread
    :cvar LOCK_DEFAULT_TIMEOUT: how many seconds to wait for acquiring a lock on the resource.
    :type LOCK_DEFAULT_TIMEOUT: int or float
    """
    __locking_thread_id = None
    LOCK_DEFAULT_TIMEOUT = 60  # TODO take this variable from the global kTBS conf file

    def _get_semaphore(self):
        """Return the semaphore for this resource.

        We attempt to initialize the semaphore with a value of 1.
        However, if it already exists we don't change the semaphore value,
        but take it as is.

        :return: semaphore for this resource.
        :rtype: posix_ipc.Semaphore
        """
        return posix_ipc.Semaphore(name=get_semaphore_name(self.uri),
                                   flags=posix_ipc.O_CREAT,
                                   initial_value=1)

    @contextmanager
    def lock(self, resource, timeout=None):
        """Lock the current resource (self) with a semaphore.

        Currently, the resources locked are ktbs root and ktbs base. To change
        any other resources (traces, models, obsels, ...) requires getting a ktbs
        root or ktbs base semaphore.

        :param resource: the resource that asks for the lock.
        :param timeout: maximum time to wait on acquire() until a BusyError is raised.
        :type timeout: int or float
        :raise TypeError: if `resource` no longer exists.
        :raise posix_ipc.BusyError: if we fail to acquire the semaphore until timeout.
        """
        if timeout is None:
            timeout = self.LOCK_DEFAULT_TIMEOUT

        # If the current thread wants to access the locked resource it is good to go.
        # This should only happen when the thread wants to lock the resource further down the call stack.
        if self.__locking_thread_id == current_thread().ident:
            yield

        # Else, either another thread wants to access the resource (and it will wait until the lock is released),
        # or the current thread wants to access the resource and it is not locked yet.
        else:
            semaphore = self._get_semaphore()

            try:  # acquire the lock, re-raise BusyError with info if it fails
                semaphore.acquire(timeout)
                if posix_ipc.SEMAPHORE_VALUE_SUPPORTED:
                    assert semaphore.value == 0, "This lock is corrupted"
                self.__locking_thread_id = thread_id = current_thread().ident
                LOG.debug("%s locked   by %s--%s", self, PID, thread_id)

                try:  # catch exceptions occurring after the lock has been acquired
                    # Make sure the resource still exists (it could have been deleted by a concurrent process).
                    if len(resource.state) == 0:
                        _mark_as_deleted(resource)
                        raise TypeError('The resource <{uri}> no longer exists.'.format(uri=resource.get_uri()))
                    yield
                except:
                    LOG.debug("%s        in %s--%s got an exception", self, PID, thread_id)
                    raise
                finally:  # make sure we exit properly by releasing the lock
                    self.__locking_thread_id = None
                    semaphore.release()
                    semaphore.close()
                    LOG.debug("%s released by %s--%s", self, PID, thread_id)

            except posix_ipc.BusyError:
                thread_id = self.__locking_thread_id if self.__locking_thread_id else 'Unknown'
                error_msg = 'The resource <{res_uri}> is locked by thread {thread_id}.'.format(res_uri=self.uri,
                                                                                               thread_id=thread_id)
                raise posix_ipc.BusyError(error_msg)

    @contextmanager
    def edit(self, parameters=None, clear=None, _trust=False):
        """I override :meth:`rdfrest.cores.ICore.edit`.
        """
        with self.lock(self), super(WithLockMixin, self).edit(parameters, clear, _trust) as editable:
            yield editable

    def post_graph(self, graph, parameters=None,
                   _trust=False, _created=None, _rdf_type=None):
        """I override :meth:`rdfrest.cores.mixins.GraphPostableMixin.post_graph`.
        """
        with self.lock(self):
            return super(WithLockMixin, self).post_graph(graph, parameters,
                                                         _trust, _created, _rdf_type)

    def delete(self, parameters=None, _trust=False):
        """I override :meth:`rdfrest.cores.local.EditableCore.delete`.
        """
        root = self.get_root()
        with root.lock(self), self.lock(self):
            super(WithLockMixin, self).delete(parameters, _trust)

    def ack_delete(self, parameters):
        """I override :meth:`rdfrest.util.EditableCore.ack_delete`.
        """
        super(WithLockMixin, self).ack_delete(parameters)
        self._get_semaphore().unlink()  # remove the semaphore from this resource as it no longer exists

    @classmethod
    def create(cls, service, uri, new_graph):
        """ I implement :meth:`rdfrest.cores.local.ILocalCore.creare`.

        After checking that the resource we create is correct,
        I ensure that the corresponding lock exists and is correctly set.
        If the semaphore already existed and was *not* correctly set,
        (i.e. with a value of 1), I raise a ValueError.

        .. note::

            It is possible that the semaphore exists
            if an old version of the service
            forgot to clean it after deleting the resource,
            or was left in an inconsistent state.

            It is then tempting to force the value of that semaphore to 1,
            so that such leftovers do not prevent a new service to run.
            However this is unsafe: imagine that

            * P1 creates the resources, and acquires the semaphore,

            * at the same time P2 creates the same resource,

            * P2 sees the semaphore value is 0, it forces it to 1,

            * finally, P1 releases the semaphore, setting its value to 2,
              defeating its purpose of being a lock.

            This scenario can be prevented if the creation of the resource
            is itself protected by a "higher" lock
            (usually the parent resource).
            This sounds like a good thing to do,
            but can not always be guaranteed
            (typically, service root resources have no parent to protect them).

            So this implementation stays on the safe side by making no assumption.
            Subclasses may override `create_lock` to force its value
            if they now they are safe to do so.
        """
        super(WithLockMixin, cls).create(service, uri, new_graph)
        sem = cls.create_lock(uri)
        if posix_ipc.SEMAPHORE_VALUE_SUPPORTED and sem.value != 1:
            # can happen if the semaphore already existed
            raise ValueError("Something's wrong: "
                             "semaphore for <{}> has value != 1"
                             .format(uri))
            # NB: the fact that semaphore.value == 1 is not a 100% proof
            # that everything is fine --
            # there could be a 2nd "token" being held at the moment.
            # But this test is better than nothing...
        sem.close()

    @classmethod
    def create_lock(cls, uri):
        """ I create the lock for the resource with the given uri.

        :param uri: the URI of the resource owning the lock
        :return: the created semaphore
        """
        semaphore = posix_ipc.Semaphore(name=get_semaphore_name(uri),
                                        flags=posix_ipc.O_CREAT,
                                        initial_value=1) # if it doesn't exist
        return semaphore
