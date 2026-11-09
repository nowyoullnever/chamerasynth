"""Host-only normalized sine-wave generation for the synth integration model.

The caller supplies sample rate, channel count, and frame count. None is a
claim about the Charmera firmware or physical output path. Generated floats are
only test data for ``MockAudioBackend``; a target PCM format/ABI is unresolved.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi, sin

from tools.synth_integration_model import PcmBuffer


class SineConfigurationError(ValueError):
    """Raised when a host-side waveform request is not mathematically valid."""


@dataclass(frozen=True)
class SineWaveRequest:
    sample_rate_hz: float
    frequency_hz: float
    frame_count: int
    amplitude: float = 1.0
    phase_radians: float = 0.0


def _validate(request: SineWaveRequest) -> None:
    if request.sample_rate_hz <= 0:
        raise SineConfigurationError("sample_rate_hz must be positive")
    if request.frequency_hz < 0:
        raise SineConfigurationError("frequency_hz must not be negative")
    if request.frame_count <= 0:
        raise SineConfigurationError("frame_count must be positive")
    if not 0.0 <= request.amplitude <= 1.0:
        raise SineConfigurationError("amplitude must be within normalized range [0, 1]")


def generate_normalized_sine(request: SineWaveRequest) -> tuple[float, ...]:
    """Return deterministic host-normalized samples in [-amplitude, amplitude]."""
    _validate(request)
    step = 2.0 * pi * request.frequency_hz / request.sample_rate_hz
    return tuple(request.amplitude * sin(request.phase_radians + step * index) for index in range(request.frame_count))


def make_mock_pcm_buffer(token: int, channels: int, request: SineWaveRequest) -> PcmBuffer:
    """Create a mock-only buffer; no firmware sample representation is implied."""
    if token < 0:
        raise SineConfigurationError("token must not be negative")
    if channels <= 0:
        raise SineConfigurationError("channels must be positive")
    return PcmBuffer(token=token, frames=generate_normalized_sine(request), channels=channels)
