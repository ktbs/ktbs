from .test_ktbs_engine import KtbsTestCase
from unittest import skipUnless
from pytest import raises as assert_raises

from ktbs.namespace import KTBS
from ktbs.engine.trace_stats import NS


class TestKtbsTraceObsels(KtbsTestCase):
    """Test features of obsel collections."""

    def setup_method(self):
        super(TestKtbsTraceObsels, self).setup_method()
        self.base = b = self.my_ktbs.create_base("b/")
        self.model = m = b.create_model("m")
        self.ot1 = ot1 = m.create_obsel_type("#OT1")
        self.ot2 = ot2 = m.create_obsel_type("#OT2")
        self.trace = t = b.create_stored_trace("t/", m,
                                               origin="1970-01-01T00:00:00Z")
        self.filtered = f = b.create_computed_trace("f/", KTBS.filter,
                                                    {"otypes": ot1.uri },
                                                    [t],)
        self.filtered2 = f2 = b.create_computed_trace("f2/", KTBS.filter,
                                                    {"after": 1 },
                                                    [f],)
        o01 = t.create_obsel("o01", ot1, 0)


    def test_stats_update_on_new_obsel(self):
        assert_stat(self.trace, NS.obselCount, 1)
        assert_stat(self.trace, NS.minTime, 0)
        assert_stat(self.trace, NS.maxTime, 0)

        self.trace.create_obsel("o02", self.ot2, 4)

        assert_stat(self.trace, NS.obselCount, 2)
        assert_stat(self.trace, NS.minTime, 0)
        assert_stat(self.trace, NS.maxTime, 4)

        self.trace.create_obsel("o03", self.ot1, 2)

        assert_stat(self.trace, NS.obselCount, 3)
        assert_stat(self.trace, NS.minTime, 0)
        assert_stat(self.trace, NS.maxTime, 4)

    def test_stats_update_when_parameters_change(self):

        assert_stat(self.filtered, NS.obselCount, 1)
        assert_stat(self.filtered, NS.minTime, 0)
        assert_stat(self.filtered, NS.maxTime, 0)

        self.filtered.set_parameter("otypes", self.ot2.uri)

        assert_stat(self.filtered, NS.obselCount, 0)

    def test_stats_update_when_source_obsels_changes(self):

        assert_stat(self.filtered, NS.obselCount, 1)
        assert_stat(self.filtered, NS.minTime, 0)
        assert_stat(self.filtered, NS.maxTime, 0)

        self.trace.create_obsel("o02", self.ot2, 4)

        assert_stat(self.filtered, NS.obselCount, 1)
        assert_stat(self.filtered, NS.minTime, 0)
        assert_stat(self.filtered, NS.maxTime, 0)

        self.trace.create_obsel("o03", self.ot1, 2)

        assert_stat(self.filtered, NS.obselCount, 2)
        assert_stat(self.filtered, NS.minTime, 0)
        assert_stat(self.filtered, NS.maxTime, 2)

    def test_stats_update_when_indirect_source_obsels_changes(self):

        assert_stat(self.filtered2, NS.obselCount, 0)

        self.trace.create_obsel("o02", self.ot2, 4)

        assert_stat(self.filtered2, NS.obselCount, 0)

        self.trace.create_obsel("o03", self.ot1, 2)

        assert_stat(self.filtered2, NS.obselCount, 1)
        assert_stat(self.filtered2, NS.minTime, 2)
        assert_stat(self.filtered2, NS.maxTime, 2)

    def test_stats_update_when_source_parameters_change(self):

        assert_stat(self.filtered2, NS.obselCount, 0)

        self.trace.create_obsel("o02", self.ot2, 4)

        assert_stat(self.filtered2, NS.obselCount, 0)

        self.filtered.set_parameter("otypes", self.ot2.uri)

        assert_stat(self.filtered2, NS.obselCount, 1)
        assert_stat(self.filtered, NS.maxTime, 4)
        assert_stat(self.filtered, NS.minTime, 4)

    def test_origin_when_source_origin_changes(self):
        # NB: this test is not related to stats,
        # but I it checks a bug that I discover while working on #69

        assert str(self.filtered.origin) == "1970-01-01T00:00:00Z"

        self.trace.origin = "2000-01-01T00:00:00Z"

        self.filtered.force_state_refresh()
        assert str(self.filtered.origin) == "2000-01-01T00:00:00Z"

    def test_origin_when_indirect_source_origin_changes(self):
        # NB: this test is not related to stats,
        # but I it checks a bug that I discover while working on #69

        assert str(self.filtered.origin) == "1970-01-01T00:00:00Z"

        self.trace.origin = "2000-01-01T00:00:00Z"

        self.filtered2.force_state_refresh()
        assert str(self.filtered2.origin) == "2000-01-01T00:00:00Z"

def assert_stat(trace, prop, nbobs):
    g = trace.trace_statistics.get_state()
    got = g.value(trace.uri, prop).value
    assert got == nbobs
