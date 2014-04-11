from test_ktbs_engine import KtbsTestCase
from ktbs.engine.base import Base
from ktbs.engine.base import get_lock
from nose.tools import assert_raises
import posix_ipc


class TestLocking(object):
    """Test locking without being in a kTBS context."""

    def test_concurrence(self):
        """Test locking implementation.

        A semaphore is opened with an initial value of 1 and acquired immediately,
        leading the number of semaphore value to 0.
        Then, we test get_lock() by expecting it to fail to acquire the same semaphore.
        """
        semaphore = posix_ipc.Semaphore(name='/pseudo_base', flags=posix_ipc.O_CREAT, initial_value=1)
        assert semaphore.value == 1
        semaphore.acquire()

        pseudo_base_name = 'pseudo_base'
        with assert_raises(posix_ipc.BusyError):
            with get_lock(pseudo_base_name, timeout=1):
                pass

        semaphore.release()
        semaphore.close()


class TestKtbsBaseLocking(KtbsTestCase):
    """Test locking in the kTBS context."""

    def test_concurrent_delete(self):
        """Tries to delete a base that is currently being locked."""
        new_base = self.my_ktbs.create_base()

        # Make a semaphore to lock the previously created base
        sem_name = str('/' + new_base.uri.replace('/', '-'))
        semaphore = posix_ipc.Semaphore(name=sem_name, flags=posix_ipc.O_CREAT, initial_value=1)
        assert semaphore.value == 1
        semaphore.acquire()  # Bring the semaphore value to 0, blocking any other acquire() before any release()

        # Tries to get a semaphore and delete a base,
        # it should block on the acquire() and raise a BusyError because a timeout is set.
        with assert_raises(posix_ipc.BusyError):
            base = Base(self.service, new_base.uri)
            base.delete()

        # Finally closing the semaphore we created for testing purpose.
        semaphore.release()
        semaphore.close()
