from test_ktbs_engine import KtbsTestCase
from nose.tools import assert_raises

from ktbs.engine.lock import WithLockMixin

import posix_ipc

# Set the lock timeout to 1 s in order to speed up the tests
WithLockMixin.LOCK_DEFAULT_TIMEOUT = 1


class KtbsRootTestCase(KtbsTestCase):
    def tearDown(self):
        """Override :meth:`KtbsTestCase.tearDown`

        Adds semaphore unlinking at the end of each test.
        """
        semaphore = self.my_ktbs._get_semaphore()
        super(KtbsRootTestCase, self).tearDown()
        semaphore.unlink()


class TestKtbsRootLocking(KtbsRootTestCase):
    """Test locking for the kTBS root."""

    def test_lock_has_semaphore(self):
        """Test if KtbsRoot.lock() really acquires the semaphore."""
        semaphore = posix_ipc.Semaphore(name=self.my_ktbs._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=1)
        assert semaphore.value == 1

        with self.my_ktbs.lock(self.my_ktbs):
            assert self.my_ktbs._get_semaphore().value == 0

            with assert_raises(posix_ipc.BusyError):
                semaphore.acquire(WithLockMixin.LOCK_DEFAULT_TIMEOUT)

    def test_lock_cant_get_semaphore(self):
        """Make sure KtbsRoot.lock() get stuck if the semaphore is already in use."""
        semaphore = posix_ipc.Semaphore(name=self.my_ktbs._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=0)
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            with self.my_ktbs.lock(self.my_ktbs):
                pass

        semaphore.release()

    def test_edit_locked_root(self):
        """Test that a KtbsRoot.edit() fails if the root is already locked."""
        semaphore = posix_ipc.Semaphore(name=self.my_ktbs._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=0)
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            self.my_ktbs.label += '_test_edit_label'

        semaphore.release()

    def test_edit_successful(self):
        """Test that after a successful edit, the KtbsRoot semaphore exists and its value is 1."""
        self.my_ktbs.label += '_test_edit_label'

        # Check that the semaphore has been created.
        with assert_raises(posix_ipc.ExistentialError):
            posix_ipc.Semaphore(name=self.my_ktbs._get_semaphore_name(),
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
            posix_ipc.Semaphore(name=self.my_ktbs._get_semaphore_name(),
                                flags=posix_ipc.O_CREX)

        assert self.my_ktbs._get_semaphore().value == 1

        base.delete()
