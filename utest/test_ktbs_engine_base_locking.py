from test_ktbs_engine import KtbsTestCase
from ktbs.engine.base import Base
from nose.tools import assert_raises
import posix_ipc


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
        # NOTE this takes several seconds (default timeout) to do.
        with assert_raises(posix_ipc.BusyError):
            base = Base(self.service, new_base.uri)
            base.delete()

        # Finally closing the semaphore we created for testing purpose.
        semaphore.release()
        semaphore.close()


class KtbsTraceTestCase(KtbsTestCase):

    base = None
    model = None
    trace = None

    def setUp(self):
        super(KtbsTraceTestCase, self).setUp()
        self.base = self.my_ktbs.create_base()
        self.model = self.base.create_model()
        self.trace = self.base.create_stored_trace(None, self.model)

    def tearDown(self):
        super(KtbsTraceTestCase, self).tearDown()
        self.base = None
        self.model = None
        self.trace = None


class TestKtbsInBaseLocking(KtbsTraceTestCase):
    """Test InBase locking in a kTBS context."""

    def test_delete_trace(self):
        sem_name = str('/' + self.base.get_uri().replace('/', '-'))
        sem = posix_ipc.Semaphore(name=sem_name, flags=posix_ipc.O_CREAT, initial_value=1)
        sem.acquire()
        try:
            assert sem.value == 0
            with assert_raises(posix_ipc.BusyError):
                self.trace.delete()
        finally:
            sem.release()
            sem.close()
