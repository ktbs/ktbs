from .test_ktbs_engine import KtbsTestCase
from unittest import skipUnless
from pytest import raises as assert_raises

from ktbs.engine.lock import WithLockMixin
from ktbs.engine.lock import get_semaphore_name
from ktbs.engine.service import make_ktbs

import posix_ipc

# Set the lock timeout to 1 s in order to speed up the tests
WithLockMixin.LOCK_DEFAULT_TIMEOUT = 0

SKIP_MSG_SEMAPHORE_VALUE = "Platform doesn't support getting the semaphore value"


#@skipUnless(posix_ipc.SEMAPHORE_VALUE_SUPPORTED, SKIP_MSG_SEMAPHORE_VALUE)
class KtbsRootTestCase(KtbsTestCase):

    def setup_method(self):
        # Run the kTBS on another from the other tests to prevent reusing existing semaphores
        self.my_ktbs = make_ktbs("http://localhost:54321/")
        self.service = self.my_ktbs.service

    def teardown_method(self):
        """Override :meth:`KtbsTestCase.teardown_method`

        Adds semaphore unlinking at the end of each test.
        """
        semaphore = self.my_ktbs._get_semaphore()
        super(KtbsRootTestCase, self).teardown_method()
        semaphore.unlink()


@skipUnless(posix_ipc.SEMAPHORE_VALUE_SUPPORTED, SKIP_MSG_SEMAPHORE_VALUE)
class TestKtbsRootLocking(KtbsRootTestCase):
    """Test locking for the kTBS root."""

    def test_lock_has_semaphore(self):
        """Test if KtbsRoot.lock() really acquires the semaphore."""
        semaphore = posix_ipc.Semaphore(name=get_semaphore_name(self.my_ktbs.uri),
                                        flags=posix_ipc.O_CREAT,
                                        initial_value=1)
        assert semaphore.value == 1

        with self.my_ktbs.lock(self.my_ktbs):
            assert self.my_ktbs._get_semaphore().value == 0

            with assert_raises(posix_ipc.BusyError):
                semaphore.acquire(WithLockMixin.LOCK_DEFAULT_TIMEOUT)

    def test_lock_cant_get_semaphore(self):
        """Make sure KtbsRoot.lock() get stuck if the semaphore is already in use."""
        semaphore = posix_ipc.Semaphore(name=get_semaphore_name(self.my_ktbs.uri),
                                        flags=posix_ipc.O_CREAT,
                                        initial_value=1)
        semaphore.acquire()
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            with self.my_ktbs.lock(self.my_ktbs):
                pass

        semaphore.release()

    def test_edit_locked_root(self):
        """Test that a KtbsRoot.edit() fails if the root is already locked."""
        semaphore = posix_ipc.Semaphore(name=get_semaphore_name(self.my_ktbs.uri),
                                        flags=posix_ipc.O_CREAT,
                                        initial_value=1)
        semaphore.acquire()
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            self.my_ktbs.label += '_test_edit_label'

        semaphore.release()

    def test_edit_successful(self):
        """Test that after a successful edit, the KtbsRoot semaphore exists and its value is 1."""
        self.my_ktbs.label += '_test_edit_label'

        # Check that the semaphore has been created.
        with assert_raises(posix_ipc.ExistentialError):
            posix_ipc.Semaphore(name=get_semaphore_name(self.my_ktbs.uri),
                                flags=posix_ipc.O_CREX)

        assert self.my_ktbs._get_semaphore().value == 1

    def test_post_locked_base(self):
        """Test that a KtbsRoot post fails if the KtbsRoot is already locked."""
        semaphore = self.my_ktbs._get_semaphore()
        semaphore.acquire()

        with assert_raises(posix_ipc.BusyError):
            self.my_ktbs.create_base()

        semaphore.release()

    def test_post_successful(self):
        """Test that after a successful post, the KtbsRoot semaphore exists and its value is 1."""
        base = self.my_ktbs.create_base()

        with assert_raises(posix_ipc.ExistentialError):
            posix_ipc.Semaphore(name=get_semaphore_name(self.my_ktbs.uri),
                                flags=posix_ipc.O_CREX)

        assert self.my_ktbs._get_semaphore().value == 1

        base.delete()
