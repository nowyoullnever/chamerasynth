import unittest

from tools.event_lifecycle_model import INNER_UPDATE_REQUEST, simulate


class EventLifecycleModelTests(unittest.TestCase):
    def test_observed_stock_slice_relays_5025_to_updater_and_resumes_loop(self):
        trace = simulate("stock", [INNER_UPDATE_REQUEST])
        self.assertEqual(trace.updater_calls, 1)
        self.assertIn("outer-send:0x108", trace.events)
        self.assertEqual(trace.loop_returns, 2)

    def test_empty_handler_loses_modelled_update_reachability(self):
        trace = simulate("naive", [INNER_UPDATE_REQUEST])
        self.assertEqual(trace.updater_calls, 0)
        self.assertNotIn("outer-send:0x108", trace.events)

    def test_relay_design_preserves_only_the_modelled_update_path(self):
        trace = simulate("update-relay-model", [0x7000, INNER_UPDATE_REQUEST])
        self.assertEqual(trace.updater_calls, 1)
        self.assertIn("synth-inner-receive:0x7000", trace.events)
        self.assertIn("synth-relay-return:update-request", trace.events)

    def test_no_update_event_does_not_invent_an_updater_call(self):
        trace = simulate("update-relay-model", [0x7000])
        self.assertEqual(trace.updater_calls, 0)
