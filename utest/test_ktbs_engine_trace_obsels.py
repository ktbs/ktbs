from .test_ktbs_engine import KtbsTestCase
from unittest import skipUnless
from pytest import raises as assert_raises

from ktbs.engine.lock import WithLockMixin
from ktbs.engine.lock import get_semaphore_name
from ktbs.engine.service import make_ktbs


class TestKtbsTraceObsels(KtbsTestCase):
    """Test features of obsel collections."""

    def setup(self):
        super(TestKtbsTraceObsels, self).setup()
        self.base = b = self.my_ktbs.create_base("b/")
        self.model = m = b.create_model("m")
        self.ot = ot = m.create_obsel_type("#OT1")
        self.trace = t = b.create_stored_trace("t/", m,
                                               origin="1970-01-01T00:00:00Z")
        t.pseudomon_range = 2000
        self.obsels = []
        for i in range(5):
            self.obsels.append(
                t.create_obsel('o%s' % i, ot, 1000 * i)
            )

    def test_etags(self):
        t = self.trace
        oc = t.obsel_collection
        etag = oc.etag
        mstag = oc.str_mon_tag # monotonic-stable tag
        pstag = oc.pse_mon_tag # pseudomonotonic-stable tag

        def get_etags(**params):
            if not params:
                return list(oc.iter_etags())
            else:
                return oc.get_state(params).etags

        assert get_etags() == [ etag ]
        assert get_etags(limit=100) == [etag,]
        assert get_etags(limit=1) == [etag, mstag, pstag,]
        assert get_etags(limit=2) == [etag, mstag, pstag,]
        assert get_etags(limit=3) == [etag, mstag,]
        assert get_etags(limit=4) == [etag, mstag,]
        assert get_etags(limit=5) == [etag,]
        assert get_etags(limit=1, offset=1) == [etag, mstag, pstag,]
        assert get_etags(limit=1, offset=2) == [etag, mstag,]
        assert get_etags(limit=1, offset=3) == [etag, mstag,]
        assert get_etags(limit=1, offset=4) == [etag,]
        assert get_etags(limit=1, offset=5) == [etag,]
        assert get_etags(before=self.obsels[0]) == [etag, mstag, pstag,]
        assert get_etags(before=self.obsels[1]) == [etag, mstag, pstag,]
        assert get_etags(before=self.obsels[2]) == [etag, mstag,]
        assert get_etags(before=self.obsels[3]) == [etag, mstag,]
        assert get_etags(before=self.obsels[4]) == [etag, mstag,]
        assert get_etags(after=self.obsels[-1]) == [etag,]
