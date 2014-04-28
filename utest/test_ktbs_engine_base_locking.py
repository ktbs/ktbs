from ktbs.namespace import KTBS
from test_ktbs_engine import KtbsTestCase
from ktbs.engine import base
from ktbs.engine.base import Base
from nose.tools import assert_raises

from rdflib.graph import Graph
from rdflib import RDF, BNode, Literal
from uuid import uuid4

import posix_ipc


# Set the lock timeout to 1 s in order to speed up the tests
base.LOCK_DEFAULT_TIMEOUT = 1


def get_random_uri():
    return str(uuid4()) + '/'


class TestKtbsBaseLocking(KtbsTestCase):
    """Test locking in the kTBS context."""

    def test_lock_has_semaphore(self):
        """Test if Base.lock() really acquires the semaphore."""
        new_base = self.my_ktbs.create_base(get_random_uri())
        semaphore = posix_ipc.Semaphore(name=new_base._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=1)
        with new_base.lock(new_base):
            assert new_base._get_semaphore().value == 0

            with assert_raises(posix_ipc.BusyError):
                semaphore.acquire(2)  # try to acquire the semaphore, fail if not available after 2 seconds

    def test_lock_cant_get_semaphore(self):
        """Make sure Base.lock() get stuck if the semaphore is already in use."""
        new_base = self.my_ktbs.create_base(get_random_uri())
        semaphore = posix_ipc.Semaphore(name=new_base._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=0)
        assert semaphore.value == 0
        with assert_raises(posix_ipc.BusyError):
            with new_base.lock(new_base):
                pass

    def test_concurrent_delete(self):
        """Tries to delete a base that is currently being locked."""
        new_base = self.my_ktbs.create_base(get_random_uri())

        # Make a semaphore to lock the previously created base
        semaphore = posix_ipc.Semaphore(name=new_base._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=0)
        assert semaphore.value == 0

        # Tries to get a semaphore and delete a base,
        # it should block on the acquire() and raise a BusyError because a timeout is set.
        # NOTE this takes several seconds (default timeout) to do.
        with assert_raises(posix_ipc.BusyError):
            base = Base(self.service, new_base.uri)
            base.delete()

        # Finally closing the semaphore we created for testing purpose.
        semaphore.release()
        semaphore.close()

    def test_concurrent_edit(self):
        new_base = self.my_ktbs.create_base(get_random_uri())

        semaphore = posix_ipc.Semaphore(name=new_base._get_semaphore_name(),
                                        flags=posix_ipc.O_CREX,
                                        initial_value=1)

        new_model = new_base.create_model()
        new_trace = new_base.create_stored_trace(None, new_model)

        semaphore.acquire()
        assert semaphore.value == 0

        with assert_raises(posix_ipc.BusyError):
            with new_base.edit() as editable:
                pass


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
