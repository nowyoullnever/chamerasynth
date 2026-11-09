# Phase 6 — audio driver recovery

Status: no verified PCM/hardware driver interface. This is static evidence from retained Phase 5 Ghidra pseudocode only.

## Recovered service path

```text
WAV-handle lookup / request 0x1e844
  -> 0x25984(..., 0x10000100 or 0x10000101, 0x1c-byte request)
  -> audio task 0x13110 / 0x25a38 receive
  -> 0x12f0c request-state setup
  -> 0x133f0(state + 4, service state, buffer table)
  -> indirect call through *(state + 8)              [unresolved target]
```

| VA | Verified retained behavior | Boundary |
| --- | --- | --- |
| `0x13110` / file `0x13310` | Receives `0x10000100`/`0x10000101` and calls `0x12f0c` | Message values are not PCM-format proof |
| `0x12f0c` / file `0x1310c` | Reads request offsets `+2/+8/+0xc/+0x10`; sets states and `0x1000`, `0x800`, or `0x480` size candidates; posts status through `0x25984` | Field types/units are unresolved |
| `0x12e48` | Waits/clears state and frees a primary pointer plus buffer-pointer array | Lifecycle evidence, not hardware identity |
| `0x12bd0` / file `0x12dd0` | Has `0x1000` wrap-style arithmetic and event/queue calls | Strong ring-buffer-worker candidate; no device proof |
| `0x133f0`, state `+8` target | Direct/indirect backend handoff | **Unresolved lowest-level target** |

No retained evidence proves WAV decode, PCM width, sample rate, channel count, DAC, PWM, DMA, interrupt completion, speaker enable, or continuous streaming. Generalplus/ZTKVR sources may guide a later search but do not establish Charmera wiring or ABI.

## HAL consequence

The included mock Audio HAL exposes opaque-buffer submit/start/stop/status/release semantics so DSP code can be tested without inventing a driver. It intentionally leaves sample rate, channel count, and sample representation untyped. It does not call `0x1e844`, `0x12f0c`, or any hardware address. A real adapter may be added only after the `0x133f0` body and the function pointer installed at state `+8` are recovered from an authorized firmware import.
