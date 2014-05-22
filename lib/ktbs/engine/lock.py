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
from threading import current_thread
from contextlib import contextmanager


class WithLockMixin(object):
    """ I provide methods to lock a resource.

    :cvar int __locking_thread_id: id of the thread
    :cvar LOCK_DEFAULT_TIMEOUT: how many seconds to wait for acquiring a lock on the resource.
    :type LOCK_DEFAULT_TIMEOUT: int or float
    """
    __locking_thread_id = None
    LOCK_DEFAULT_TIMEOUT = 60  # TODO take this variable from the global kTBS conf file

    def _get_semaphore_name(self):
        """Return the semaphore name for this resource.

        :return: semaphore name.
        :rtype: str
        """
        return str('/' + self.uri.replace('/', '-'))

    def _get_semaphore(self):
        """Return the semaphore for this resource.

        We attempt to initialize the semaphore with a value of 1.
        However, if it already exists we don't change the semaphore value,
        but take it as is.

        :return: semaphore for this resource.
        :rtype: posix_ipc.Semaphore
        """
        return posix_ipc.Semaphore(name=self._get_semaphore_name(),
                                   flags=posix_ipc.O_CREAT,
                                   initial_value=1)

    @contextmanager
    def lock(self, resource, timeout=None):
        """Lock the current resource (self) with a semaphore.

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
                self.__locking_thread_id = current_thread().ident

                try:  # catch exceptions occurring after the lock has been acquired
                    yield
                finally:  # make sure we exit properly by releasing the lock
                    self.__locking_thread_id = None
                    semaphore.release()
                    semaphore.close()

            except posix_ipc.BusyError:
                thread_id = self.__locking_thread_id if self.__locking_thread_id else 'Unknown'
                error_msg = 'The resource <{res_uri}> is locked by thread {thread_id}.'.format(res_uri=self.uri,
                                                                                               thread_id=thread_id)
                raise posix_ipc.BusyError(error_msg)
