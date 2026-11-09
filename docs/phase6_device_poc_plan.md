# Phase 6 — first device POC preparation

No device operation, SD installation, flash-ready image, or modified stock firmware exists in this phase.

## Test A — resource-only playback change

**Recommendation: simplest useful first hardware candidate, but not approved.** It would retain stock control flow and use the existing resource lookup/playback path rather than introducing a new event handler or register access.

Retained evidence: `0x1e234` looks up `CLICK.WAV`, `POWERON_AUDIO.WAV`, `POWEROFF_AUDIO.WAV`, `BEEP.WAV`, and `IMG.WAV` through `0x1310`; the results are stored as 16-bit handle candidates at table VA `0x110284 + 4,6,8,c,e`. `0x1e844` selects a stored handle and builds a 0x1c request for `0x25984`.

This does **not** recover the BEEP payload range, RIFF/container format, allocation size, alignment, pointer/length table, checksum, or a resource validator. The new `tools/resource_replacement_prototype.py` accepts only an evidence-backed `analysis-only` manifest: exact source SHA-256, fixed-size expected/replacement bytes, alignment, and every permitted metadata range. It writes a separate copy and rejects source mismatch, overlap, same-path output, or a change outside declared ranges. It is not a Charmera manifest and cannot make a flash-ready package.

Before deployment: recover the resource table/dataflow from an authorized source image; prove all payload and metadata ranges; generate/review copy-only diff and restoration result; establish updater length/erase behavior; and establish an external recovery path. A stock restore file is not recovery proof: a bad boot can block access to the SD updater, and no practical external SPI recovery path is established.

## Test B — button-triggered stock playback

**Not approved.** `0x6134` calls `0x1e844(2)` during startup. The `0x1c9c4` state machine has `0x7000`-family paths that call `0x1e844(0)`. Neither is a recovered physical button mapping; selector-to-resource mapping, GPIO/IRQ source, debounce, stack ABI, service-state guard, and queue ownership are unresolved.

Before deployment: trace a physical button ISR/poll path through event production to one known `0x700x` handler; map selector to resource; prove `0x1e844` preconditions; establish a safe UI-only hook/payload location; and satisfy the same updater/external-recovery gate as Test A.

## Test C — generated PCM

`tools/synth_pcm_generator.py` is a deterministic host-only normalized sine generator. Its sample-rate and channel inputs are caller-provided test configuration, not Charmera facts. It can submit data to the mock audio backend and verify ownership/release lifecycle.

The hardware path remains `0x12f0c → 0x133f0 → *(state+8)`. PCM representation, sample rate, channel count, DMA/DAC/PWM, completion interrupt, continuous buffering, and driver ABI are unresolved. No generated PCM should be sent to firmware until the `0x133f0` body and indirect target are recovered.

## Recovery decision

The correct next action is still offline: re-obtain an authorized original image and run `ExportPhase6Boundaries.java` to resolve resource, button, queue, and audio backend dataflow. Only after the above gates can Test A be reviewed as a first physical microSD experiment in Phase 7 under explicit authorization. Test B and Test C are later experiments.
