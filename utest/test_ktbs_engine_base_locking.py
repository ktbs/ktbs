from test_ktbs_engine import KtbsTestCase
from nose.tools import assert_raises

from ktbs.engine import base
from ktbs.namespace import KTBS

import posix_ipc


# Set the lock timeout to 1 s in order to speed up the tests
base.LOCK_DEFAULT_TIMEOUT = 1


# Tests for BASE

class KtbsBaseTestCase(KtbsTestCase):

    tmp_base = None
    tmp_base_name = 'tmp_base/'

    def setUp(self):
        super(KtbsBaseTestCase, self).setUp()
        self.tmp_base = self.my_ktbs.create_base(self.tmp_base_name)

    def tearDown(self):
        super(KtbsBaseTestCase, self).tearDown()
        self.tmp_base.delete()


class TestKtbsBaseLocking(KtbsBaseTestCase):
    """Test locking in the kTBS context."""

    def test_lock_has_semaphore(self):
        """Test if Base.lock() really acquires the semaphore."""
        semaphore = posix_ipc.Semaphore(name=self.tmp_base._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=1)
        assert semaphore.value == 1

        with self.tmp_base.lock(self.tmp_base):
            assert self.tmp_base._get_semaphore().value == 0

            with assert_raises(posix_ipc.BusyError):
                semaphore.acquire(base.LOCK_DEFAULT_TIMEOUT)

    def test_lock_cant_get_semaphore(self):
        """Make sure Base.lock() get stuck if the semaphore is already in use."""
        semaphore = posix_ipc.Semaphore(name=self.tmp_base._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=0)
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            with self.tmp_base.lock(self.tmp_base):
                pass

        semaphore.release()

    def test_delete_locked_base(self):
        """Tries to delete a base that is currently being locked."""
        # Make a semaphore to lock the previously created base
        semaphore = posix_ipc.Semaphore(name=self.tmp_base._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=0)
        assert semaphore.value == 0

        # Tries to get a semaphore and delete a base,
        # it should block on the acquire() and raise a BusyError because a timeout is set.
        with assert_raises(posix_ipc.BusyError):
            self.tmp_base.delete()

        # Finally closing the semaphore we created for testing purpose.
        semaphore.release()

    def test_delete_successful(self):
        """Test that a semaphore related to base no longer exists after the base has been deleted."""
        new_base = self.my_ktbs.create_base('new_base/')
        semaphore = new_base._get_semaphore()

        new_base.delete()  # should remove the semaphore related to this base

        # This will raise a posix_ipc.ExistancialError if the semaphore already exists.
        posix_ipc.Semaphore(name=semaphore.name, flags=posix_ipc.O_CREX)

        semaphore.unlink()

    def test_edit_locked_base(self):
        """Test that a base.edit() fails if the base is already locked."""
        semaphore = posix_ipc.Semaphore(name=self.tmp_base._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=0)
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            self.tmp_base.label += '_test_edit_label'

        semaphore.release()

    def test_edit_successful(self):
        """Test that after a successful edit, the base semaphore exists and its value is 1."""
        self.tmp_base.label += '_test_edit_label'

        # Check that the semaphore already exists, meaning that edit() used it.
        # If we don't check that, the semaphore value could still be 1 because we use _get_semaphore()
        # and initialize the semaphore value at 1.
        with assert_raises(posix_ipc.ExistentialError):
            posix_ipc.Semaphore(name=self.tmp_base._get_semaphore_name(),
                                flags=posix_ipc.O_CREX)

        assert self.tmp_base._get_semaphore().value == 1

    def test_post_locked_base(self):
        """Test that a base post fails if the base is already locked."""
        semaphore = self.tmp_base._get_semaphore()
        semaphore.acquire()

        with assert_raises(posix_ipc.BusyError):
            self.tmp_base.create_model()

        semaphore.release()

    def test_post_successful(self):
        """Test that after a successful post, the base semaphore exists and its value is 1."""
        model = self.tmp_base.create_model()

        with assert_raises(posix_ipc.ExistentialError):
            posix_ipc.Semaphore(name=self.tmp_base._get_semaphore_name(),
                                flags=posix_ipc.O_CREX)

        assert self.tmp_base._get_semaphore().value == 1

        model.delete()


# Tests for MODEL

class KtbsModelTestCase(KtbsBaseTestCase):
    model = None

    def setUp(self):
        super(KtbsModelTestCase, self).setUp()
        self.model = self.tmp_base.create_model()

    def tearDown(self):
        self.model.delete()
        super(KtbsModelTestCase, self).tearDown()


class TestKtbsModelLocking(KtbsModelTestCase):
    # NOTE we can't use the flag O_CREX anymore when instantiating a semaphore.
    # A semaphore already exists, because we use create_model() during setup.
    def test_edit_locked_base(self):
        """Test that a Model can't be edited if the base is locked."""
        semaphore = self.tmp_base._get_semaphore()
        semaphore.acquire()
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            self.model.label += '_test_edit_label'

        semaphore.release()

    def test_edit_successful(self):
        """Test that after an Model edit(), the semaphore has been released, i.e. its value is 1."""
        semaphore = self.tmp_base._get_semaphore()
        assert semaphore.value == 1

        self.model.label += '_test_edit_label'

        # Here, unlike in TestKtbsBASELocking.test_edit_successful, we don't check for semaphore existency.
        # The semaphore has already been created during the setup, when create_model() was called.

        assert semaphore.value == 1

    def test_delete_locked_base(self):
        """Test that a Model can't be deleted if the base is locked."""
        semaphore = self.tmp_base._get_semaphore()
        semaphore.acquire()
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            self.model.delete()

        semaphore.release()

    def test_delete_successful(self):
        """Test that the semaphore has been released after a Model delete()."""
        semaphore = self.tmp_base._get_semaphore()
        assert semaphore.value == 1

        new_model = self.tmp_base.create_model()
        new_model.delete()

        assert semaphore.value == 1


# Tests for METHOD

class KtbsMethodTestCase(KtbsBaseTestCase):

    method = None

    def setUp(self):
        super(KtbsMethodTestCase, self).setUp()
        self.method = self.tmp_base.create_method(parent=KTBS.filter)

    def tearDown(self):
        self.method.delete()
        super(KtbsMethodTestCase, self).tearDown()


class TestKtbsMethodLocking(KtbsMethodTestCase):
    def test_edit_locked_base(self):
        """Test that we can't edit a method is the base is locked."""
        semaphore = self.tmp_base._get_semaphore()
        semaphore.acquire()
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            self.method.label += '_test_edit_label'

        semaphore.release()

    def test_edit_successful(self):
        """Test that the semaphore is released after a successful edit."""
        semaphore = self.tmp_base._get_semaphore()
        assert semaphore.value == 1

        self.method.label += '_test_edit_label'

        assert semaphore.value == 1

    def test_delete_locked_base(self):
        """Test that a method can't be deleted if the base is locked."""
        semaphore = self.tmp_base._get_semaphore()
        semaphore.acquire()
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            self.method.delete()

        semaphore.release()

    def test_delete_successful(self):
        """Test that the semaphore has been released after a successful Method delete."""
        semaphore = self.tmp_base._get_semaphore()
        assert semaphore.value == 1

        new_method = self.tmp_base.create_method(parent=KTBS.filter)
        new_method.delete()

        assert semaphore.value == 1


# Tests Trace

class KtbsTraceTestCase(KtbsModelTestCase):

    trace = None

    def setUp(self):
        super(KtbsTraceTestCase, self).setUp()
        self.trace = self.tmp_base.create_stored_trace(model=self.model)

    def tearDown(self):
        self.trace.delete()
        super(KtbsTraceTestCase, self).tearDown()


class TestKtbsTraceLocking(KtbsTraceTestCase):
    def test_edit_locked_base(self):
        """Test that we can't edit a Trace if the base is locked."""
        semaphore = self.tmp_base._get_semaphore()
        semaphore.acquire()
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            self.trace.label += '_test_edit_label'

        semaphore.release()

    def test_edit_successful(self):
        """Test that the semaphore is released after a successful Trace edit."""
        semaphore = self.tmp_base._get_semaphore()
        assert semaphore.value == 1

        self.trace.label += '_test_edit_label'

        assert semaphore.value == 1

    def test_post_locked_base(self):
        """Test that we can't post on a Trace if the base is locked."""
        # Create a temporary obsel type so we can use create_obsel()
        otype = self.model.create_obsel_type('#tmp_otype')

        semaphore = self.tmp_base._get_semaphore()
        semaphore.acquire()
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            self.trace.create_obsel(type=otype, subject='tmp_subject', begin=0)

        semaphore.release()

    def test_post_successful(self):
        """Test that the semaphore is released after a successful Trace post."""
        semaphore = self.tmp_base._get_semaphore()
        assert semaphore.value == 1

        # Create a temporary obsel type so we can use create_obsel()
        otype = self.model.create_obsel_type('#tmp_otype')
        self.trace.create_obsel(type=otype, subject='tmp_subject', begin=0)

        assert semaphore.value == 1

    def test_delete_locked_base(self):
        """Test that we can't delete a Trace if the base is locked."""
        semaphore = self.tmp_base._get_semaphore()
        semaphore.acquire()
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            self.trace.delete()

        semaphore.release()

    def test_delete_successful(self):
        """Test that the semaphore is released after a successful Trace delete."""
        semaphore = self.tmp_base._get_semaphore()
        assert semaphore.value == 1

        new_trace = self.tmp_base.create_stored_trace(model=self.model)
        new_trace.delete()

        assert semaphore.value == 1
