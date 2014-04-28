from ktbs.namespace import KTBS
from test_ktbs_engine import KtbsTestCase
from ktbs.engine import base
from nose.tools import assert_raises

from rdflib.graph import Graph
from rdflib import RDF, BNode, Literal

import posix_ipc


# Set the lock timeout to 1 s in order to speed up the tests
base.LOCK_DEFAULT_TIMEOUT = 1


class KtbsBaseTestCase(KtbsTestCase):

    tmp_base = None

    def setUp(self):
        super(KtbsBaseTestCase, self).setUp()
        self.tmp_base = self.my_ktbs.create_base()

    def tearDown(self):
        super(KtbsBaseTestCase, self).tearDown()
        self.tmp_base.delete()


class TestKtbsBaseLocking(KtbsBaseTestCase):
    """Test locking in the kTBS context."""

    def test_lock_has_semaphore(self):
        """Test if Base.lock() really acquires the semaphore."""
        semaphore = posix_ipc.Semaphore(name=self.tmp_base._get_semaphore_name(),
                                        flags=posix_ipc.O_CREAT,
                                        initial_value=1)
        with self.tmp_base.lock(self.tmp_base):
            assert self.tmp_base._get_semaphore().value == 0

            with assert_raises(posix_ipc.BusyError):
                semaphore.acquire(base.LOCK_DEFAULT_TIMEOUT)

    def test_lock_cant_get_semaphore(self):
        """Make sure Base.lock() get stuck if the semaphore is already in use."""
        semaphore = posix_ipc.Semaphore(name=self.tmp_base._get_semaphore_name(),
                                        flags=posix_ipc.O_CREAT,
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
                                        flags=posix_ipc.O_CREAT,
                                        initial_value=0)
        assert semaphore.value == 0

        # Tries to get a semaphore and delete a base,
        # it should block on the acquire() and raise a BusyError because a timeout is set.
        with assert_raises(posix_ipc.BusyError):
            self.tmp_base.delete()

        # Finally closing the semaphore we created for testing purpose.
        semaphore.release()
        semaphore.unlink()

    def test_delete_successful(self):
        """Test that a semaphore related to base no longer exists after the base has been deleted."""
        new_base = self.my_ktbs.create_base('new_base/')
        semaphore = new_base._get_semaphore()

        new_base.delete()

        # This will raise a posix_ipc.ExistancialError if the semaphore already exists.
        posix_ipc.Semaphore(name=semaphore.name, flags=posix_ipc.O_CREX)

        semaphore.unlink()

    def test_edit_locked_base(self):
        """Test that an base.edit() fails if the base is already locked."""
        semaphore = posix_ipc.Semaphore(name=self.tmp_base._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=0)

        with assert_raises(posix_ipc.BusyError):
            self.tmp_base.label += '_test_change_label'

        semaphore.release()
        semaphore.unlink()

    def test_edit_successful(self):
        """Test that after a successful edit, the base semaphore exists and its value is 1."""
        self.tmp_base.label += '_test_change_label'

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
        semaphore.unlink()

    def test_post_successful(self):
        """Test that after a successful post, the base semaphore exists and its value is 1."""
        model = self.tmp_base.create_model()

        with assert_raises(posix_ipc.ExistentialError):
            posix_ipc.Semaphore(name=self.tmp_base._get_semaphore_name(),
                                flags=posix_ipc.O_CREX)

        assert self.tmp_base._get_semaphore().value == 1

        model.delete()


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
        sem = self.base._get_semaphore()
        sem.acquire()
        try:
            assert sem.value == 0
            with assert_raises(posix_ipc.BusyError):
                self.trace.delete()
        finally:
            sem.release()
            sem.close()

    def test_post_graph(self):
        model = self.base.create_model()
        otype0 = model.create_obsel_type("#MyObsel0")
        otype1 = model.create_obsel_type("#MyObsel1")
        otype2 = model.create_obsel_type("#MyObsel2")
        otype3 = model.create_obsel_type("#MyObsel3")
        otypeN = model.create_obsel_type("#MyObselN")
        self.trace = self.base.create_stored_trace(None, model, "1970-01-01T00:00:00Z", "alice")
        # purposefully mix obsel order,
        # to check whether batch post is enforcing the monotonic order
        graph = Graph()
        obsN = BNode()
        graph.add((obsN, KTBS.hasTrace, self.trace.uri))
        graph.add((obsN, RDF.type, otypeN.uri))
        obs1 = BNode()
        graph.add((obs1, KTBS.hasTrace, self.trace.uri))
        graph.add((obs1, RDF.type, otype1.uri))
        graph.add((obs1, KTBS.hasBegin, Literal(1)))
        graph.add((obs1, RDF.value, Literal("obs1")))
        obs3 = BNode()
        graph.add((obs3, KTBS.hasTrace, self.trace.uri))
        graph.add((obs3, RDF.type, otype3.uri))
        graph.add((obs3, KTBS.hasBegin, Literal(3)))
        graph.add((obs3, KTBS.hasSubject, Literal("bob")))
        obs2 = BNode()
        graph.add((obs2, KTBS.hasTrace, self.trace.uri))
        graph.add((obs2, RDF.type, otype2.uri))
        graph.add((obs2, KTBS.hasBegin, Literal(2)))
        graph.add((obs2, KTBS.hasEnd, Literal(3)))
        graph.add((obs2, RDF.value, Literal("obs2")))
        obs0 = BNode()
        graph.add((obs0, KTBS.hasTrace, self.trace.uri))
        graph.add((obs0, RDF.type, otype0.uri))
        graph.add((obs0, KTBS.hasBegin, Literal(0)))

        old_tag = self.trace.obsel_collection.str_mon_tag
        created = self.trace.post_graph(graph)
