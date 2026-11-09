"""Host-only logical model for the Phase 6 synth integration boundary.

The model preserves the observed 0x5025 -> 0x108 relationship.  It does not
model stock queue ABI, firmware execution, PCM hardware, or a confirmed camera
UI hook.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Deque, Iterable

OUTER_APPLICATION = 0x100
OUTER_UPDATER = 0x108
INNER_UPDATE_REQUEST = 0x5025


class AudioState(Enum):
    STOPPED = auto()
    RUNNING = auto()


@dataclass(frozen=True)
class PcmBuffer:
    token: int
    frames: tuple[int, ...]
    channels: int


@dataclass
class MockAudioBackend:
    state: AudioState = AudioState.STOPPED
    owned_buffers: dict[int, PcmBuffer] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def start(self) -> None:
        self.state = AudioState.RUNNING
        self.events.append("audio-start")

    def submit(self, buffer: PcmBuffer) -> None:
        if self.state is not AudioState.RUNNING:
            raise RuntimeError("audio is not running")
        if not buffer.frames or buffer.channels <= 0 or buffer.token in self.owned_buffers:
            raise ValueError("invalid or duplicate PCM buffer")
        self.owned_buffers[buffer.token] = buffer
        self.events.append(f"audio-submit:{buffer.token}")

    def release(self, token: int) -> None:
        if token not in self.owned_buffers:
            raise KeyError(token)
        del self.owned_buffers[token]
        self.events.append(f"audio-release:{token}")

    def stop(self) -> None:
        self.state = AudioState.STOPPED
        self.events.append("audio-stop")


@dataclass
class Trace:
    events: list[str] = field(default_factory=list)
    updater_calls: int = 0
    app_events: list[int] = field(default_factory=list)
    shutdowns: int = 0


class SynthIntegrationModel:
    """Logical outer dispatcher plus the proposed update-preserving boundary."""

    def __init__(self, inner_events: Iterable[int], audio: MockAudioBackend | None = None):
        self.inner: Deque[int] = deque(inner_events)
        self.outer: Deque[int] = deque([OUTER_APPLICATION])
        self.audio = audio or MockAudioBackend()
        self.trace = Trace()

    def publish_outer(self, code: int) -> None:
        self.outer.append(code)
        self.trace.events.append(f"outer-send:{code:#x}")

    def _shutdown(self) -> None:
        self.audio.stop()
        self.trace.shutdowns += 1
        self.trace.events.append("synth-shutdown")

    def _handle_inner(self, code: int) -> bool:
        self.trace.events.append(f"inner-receive:{code:#x}")
        if code == INNER_UPDATE_REQUEST:
            self.publish_outer(OUTER_UPDATER)
            self._shutdown()
            self.trace.events.append("return-for-stock-cleanup")
            return True
        self.trace.app_events.append(code)
        self.trace.events.append(f"synth-app-event:{code:#x}")
        return False

    def run(self) -> Trace:
        while self.outer:
            code = self.outer.popleft()
            self.trace.events.append(f"outer-receive:{code:#x}")
            if code == OUTER_APPLICATION:
                while self.inner:
                    if self._handle_inner(self.inner.popleft()):
                        break
                self.trace.events.append("outer-loop-resume")
            elif code == OUTER_UPDATER:
                self.trace.updater_calls += 1
                self.trace.events.append("updater-stub-call")
                self.trace.events.append("outer-loop-resume")
            else:
                self.trace.events.append(f"outer-unexpected:{code:#x}")
        return self.trace
