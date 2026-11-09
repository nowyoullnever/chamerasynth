import unittest

from tools.synth_integration_model import (
    AudioState,
    INNER_UPDATE_REQUEST,
    MockAudioBackend,
    PcmBuffer,
    SynthIntegrationModel,
)


class SynthIntegrationModelTests(unittest.TestCase):
    def test_pcm_backend_tracks_ownership_until_explicit_release(self):
        audio = MockAudioBackend()
        audio.start()
        buffer = PcmBuffer(token=7, frames=(0, 1, -1, 0), channels=1)
        audio.submit(buffer)
        self.assertEqual(audio.owned_buffers[7], buffer)
        audio.release(7)
        self.assertFalse(audio.owned_buffers)

    def test_pcm_backend_rejects_invalid_or_unowned_lifecycle(self):
        audio = MockAudioBackend()
        with self.assertRaises(RuntimeError):
            audio.submit(PcmBuffer(token=1, frames=(0,), channels=1))
        audio.start()
        with self.assertRaises(ValueError):
            audio.submit(PcmBuffer(token=1, frames=(), channels=1))
        with self.assertRaises(KeyError):
            audio.release(9)

    def test_normal_and_unexpected_application_events_remain_application_owned(self):
        model = SynthIntegrationModel([0x7000, 0xDEAD])
        trace = model.run()
        self.assertEqual(trace.app_events, [0x7000, 0xDEAD])
        self.assertEqual(trace.updater_calls, 0)
        self.assertEqual(trace.shutdowns, 0)

    def test_update_request_stops_synth_and_preserves_updater_reachability(self):
        audio = MockAudioBackend()
        audio.start()
        model = SynthIntegrationModel([0x7000, INNER_UPDATE_REQUEST], audio)
        trace = model.run()
        self.assertEqual(trace.app_events, [0x7000])
        self.assertEqual(trace.updater_calls, 1)
        self.assertEqual(trace.shutdowns, 1)
        self.assertEqual(audio.state, AudioState.STOPPED)
        self.assertIn("return-for-stock-cleanup", trace.events)
