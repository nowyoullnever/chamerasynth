# Kodak Charmera Synth Firmware — Phase 1

This repository is an **offline, read-only research foundation**.  It does not
contain a flashable image, startup code, device-control code, or scripts that
send commands to a camera.

## Layout

- `docs/`: Phase 1 evidence, assumptions, risks, and the Phase 2 gate.
- `tools/inspect_firmware.py`: reproducible passive inspection (hashes,
  header bytes, entropy, strings, and simple signature hits).
- `tests/`: offline validation for the inspection tool.
- `references/`: unmodified local clones of third-party repositories. Treat
  them as evidence, not as code to copy into a Charmera firmware.

## Safe use

Run only against a local file; the script opens it read-only:

```powershell
python tools/inspect_firmware.py references/Project-Sirius/Original_Firmware.bin --json work/firmware-inspection.json
python -m unittest discover -s tests -v
```

`--json` writes a report, never modifies its input.  The output directory is
ignored by Git. Do not add a physical camera, serial device, or flash tool to
this Phase 1 project.

## Phase 2 offline framework

`tools/firmware_inject.py` validates a source identity and manifest before it
will consider an experimental image. The committed manifest is intentionally
analysis-only, so it cannot produce an image.

```powershell
python tools/firmware_inject.py verify patches/manifest.example.toml references/Project-Sirius/Original_Firmware.bin
python tools/firmware_inject.py assemble firmware/synth_stub.S work/synth-stub
python -m unittest discover -s tests -v
```

The ARM object is an offline, hardware-neutral skeleton. It does not call a
stock driver, access MMIO, or establish a flash-safe patch point.

## Phase 3 Ghidra analysis (offline only)

Ghidra 12.2 was run locally against a newly-created payload copy, never the
source image. The analysis project and generated graph stay under ignored
`work/ghidra/`; the reproducible scripts are committed in `ghidra_scripts/`
and `tools/`.

```powershell
python tools/prepare_ghidra_payload.py references/Project-Sirius/Original_Firmware.bin work/ghidra/input/Original_Firmware.payload.bin work/ghidra/input/payload-mapping.json
.\tools\run_ghidra_analysis.ps1
python -m unittest discover -s tests -v
```

The import uses `ARM:LE:32:v4t` and logical payload base `0x0`. Its transform
(`file offset = logical VA + 0x200`) is an analysis hypothesis, not proof of a
physical runtime mapping. Phase 3 did not produce an application hook,
modified image, SD update package, device command, or flashing procedure.

## Phase 4 boundary result

Static Ghidra evidence identifies a conditional camera-handler replacement
candidate at file `0x2592c` (logical VA `0x2572c`): it is the `BL` from the
shared event loop's event `0x100` case to the stock state handler. The same
loop has a separate event `0x108` branch to the updater, so replacing the
entire loop would be unsafe. The candidate remains protected and unpatched;
tail layout and handler dependencies are unresolved.

`firmware/synth_event_handler_prototype.S` is a separate, no-MMIO ARM ELF
prototype only. It is not a firmware payload or device-compatible program.

## Phase 5 event and audio boundary

The static event relay `0x5025 -> 0x108 -> 0x21170` is documented and tested
as a host-side logical model, but the producer and condition for `0x5025` are
not recovered. Replacing the `0x2572c` call to the application handler is
therefore explicitly not approved. The WAV path reaches a software request
chain, not a verified PCM/DAC/PWM/DMA output API. See `docs/phase5_*.md` and
the phase result archives for reproducible graphs and pseudocode.

The proprietary stock firmware and third-party reference checkouts are not
distributed in this repository. Supply an authorized local copy of the stock
image only when running the offline inspection or Ghidra reproduction steps.

## Phase 6 host integration boundary

`firmware/synth/` and `firmware/hal/` now provide a host-testable synth
application and opaque-buffer audio HAL contract. They do not contain a stock
audio ABI, hardware register, firmware address, firmware patch, or runnable
device payload. The host model preserves a delivered `0x5025 -> 0x108` update
relay and returns for stock cleanup; it does not identify the event producer.

The compact Ghidra exports in phase result archives establish the audio path
only through `0x12f0c -> 0x133f0 -> *(state + 8)`. An authorized firmware
image is required to recover that backend or any safe application hook. See
`docs/phase6_*.md` for evidence boundaries and the current integration gate.

