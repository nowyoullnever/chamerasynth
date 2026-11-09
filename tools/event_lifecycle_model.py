#!/usr/bin/env python3
"""Offline logical model of the Phase 5 event path.

This does not emulate firmware or establish hardware behavior. It records only
the observed control-flow relationships needed to test integration choices:
outer 0x100 dispatches the application handler; inner 0x5025 causes that
handler to send outer 0x108; outer 0x108 calls the updater and resumes its
event loop.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Deque, Iterable

OUTER_CAMERA = 0x100
OUTER_UPDATER = 0x108
INNER_UPDATE_REQUEST = 0x5025


@dataclass
class Trace:
    events: list[str] = field(default_factory=list)
    updater_calls: int = 0
    loop_returns: int = 0


class OuterLoop:
    """Logical projection of VA 0x25668; it owns the outer event queue."""

    def __init__(self, handler: Callable[["OuterLoop", Deque[int], Trace], None], inner: Iterable[int]):
        self.handler = handler
        self.inner: Deque[int] = deque(inner)
        self.outer: Deque[int] = deque([OUTER_CAMERA])  # observed initial 0x100 signal
        self.trace = Trace()

    def send_outer(self, code: int) -> None:
        self.outer.append(code)
        self.trace.events.append(f"outer-send:{code:#x}")

    def run(self) -> Trace:
        while self.outer:
            code = self.outer.popleft()
            self.trace.events.append(f"outer-receive:{code:#x}")
            if code == OUTER_CAMERA:
                self.handler(self, self.inner, self.trace)
                self.trace.loop_returns += 1
                self.trace.events.append("outer-loop-resume")
            elif code == OUTER_UPDATER:
                self.trace.updater_calls += 1
                self.trace.events.append("updater-stub-call")
                self.trace.loop_returns += 1
                self.trace.events.append("outer-loop-resume")
            else:
                self.trace.events.append(f"outer-other:{code:#x}")
        return self.trace


def stock_handler(loop: OuterLoop, inner: Deque[int], trace: Trace) -> None:
    """Observed relevant slice of VA 0x63b0, not a full decompilation."""
    while inner:
        code = inner.popleft()
        trace.events.append(f"inner-receive:{code:#x}")
        if code == INNER_UPDATE_REQUEST:
            loop.send_outer(OUTER_UPDATER)  # VA 0x6440 -> 0x8f67c(..., 0x108)
            trace.events.append("camera-handler-return:update-request")
            return
    trace.events.append("camera-handler-return:model-drain")


def naive_replacement(_loop: OuterLoop, _inner: Deque[int], trace: Trace) -> None:
    """The rejected empty replacement at the 0x2572c call site."""
    trace.events.append("naive-handler-return")


def update_relay_synth_model(loop: OuterLoop, inner: Deque[int], trace: Trace) -> None:
    """Design model only: preserve the proven update relay, then return.

    This is deliberately not an ARM implementation. The actual inner queue
    setup, other event semantics, and synth scheduling contract are unresolved.
    """
    while inner:
        code = inner.popleft()
        trace.events.append(f"synth-inner-receive:{code:#x}")
        if code == INNER_UPDATE_REQUEST:
            loop.send_outer(OUTER_UPDATER)
            trace.events.append("synth-relay-return:update-request")
            return
    trace.events.append("synth-model-return:no-update")


def simulate(kind: str, inner_events: Iterable[int]) -> Trace:
    handlers = {
        "stock": stock_handler,
        "naive": naive_replacement,
        "update-relay-model": update_relay_synth_model,
    }
    try:
        handler = handlers[kind]
    except KeyError as error:
        raise ValueError(f"unknown model kind: {kind}") from error
    return OuterLoop(handler, inner_events).run()
