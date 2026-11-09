import math
import unittest

from tools.synth_integration_model import MockAudioBackend
from tools.synth_pcm_generator import (
    SineConfigurationError,
    SineWaveRequest,
    generate_normalized_sine,
    make_mock_pcm_buffer,
)


class SynthPcmGeneratorTests(unittest.TestCase):
    def test_generation_is_deterministic_for_caller_supplied_rate(self):
        request = SineWaveRequest(sample_rate_hz=8_000, frequency_hz=2_000, frame_count=8, amplitude=0.5)
        samples = generate_normalized_sine(request)
        self.assertEqual(samples, generate_normalized_sine(request))
        self.assertAlmostEqual(samples[0], 0.0)
        self.assertAlmostEqual(samples[1], 0.5)
        self.assertAlmostEqual(samples[2], 0.0, places=12)
        self.assertAlmostEqual(samples[3], -0.5)

    def test_normalized_amplitude_never_exceeds_requested_bound(self):
        samples = generate_normalized_sine(SineWaveRequest(44_100, 440, 128, amplitude=0.25))
        self.assertTrue(all(abs(sample) <= 0.25 for sample in samples))

    def test_invalid_host_configuration_is_rejected(self):
        for request in (
            SineWaveRequest(0, 440, 1),
            SineWaveRequest(8_000, -1, 1),
            SineWaveRequest(8_000, 440, 0),
            SineWaveRequest(8_000, 440, 1, amplitude=1.1),
        ):
            with self.assertRaises(SineConfigurationError):
                generate_normalized_sine(request)

    def test_generated_mock_buffer_obeys_submit_and_release_lifecycle(self):
        backend = MockAudioBackend()
        backend.start()
        buffer = make_mock_pcm_buffer(3, 1, SineWaveRequest(48_000, 220, 16, amplitude=0.75))
        backend.submit(buffer)
        self.assertIs(backend.owned_buffers[3], buffer)
        backend.release(3)
        self.assertFalse(backend.owned_buffers)
        self.assertTrue(math.isfinite(buffer.frames[-1]))
