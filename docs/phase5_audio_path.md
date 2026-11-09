# Phase 5 audio path

## Proven software-side chain

`0x1e234` (file `0x1e434`) initializes resource handles. It calls the resource-opening path for `CLICK.WAV`, `POWERON_AUDIO.WAV`, `POWEROFF_AUDIO.WAV`, `BEEP.WAV`, and `IMG.WAV`; candidate 16-bit handle slots are stored at table VA `0x110284` offsets `+4`, `+6`, `+8`, `+0xc`, `+0xe`.

The smallest observed playback-request chain is:

```text
startup 0x6134
  -> 0x1e844(2)                 select a stored WAV handle
  -> allocate/fill 0x1c request
  -> 0x25984(runtime queue, 0x10000100, request, 0x1c, ...)
  -> 0x13110 queue loop / 0x25a38 receive
  -> code 0x10000100 or 0x10000101
  -> 0x12f0c
  -> 0x133f0 and an indirect function pointer at state + 8
```

`0x1310`/`0x1298` resource lookup returns/obtains a slot or handle; it is not treated as playback proof. `0x12f0c` configures state and `0x1000`, `0x800`, or `0x480` size buffers before the indirect downstream call. This establishes a software request/service chain, not hardware output.

## Unresolved hardware path

No direct PCM decoder, sample format, mono/stereo format, DAC, PWM, DMA, or verified MMIO output write was recovered from the traced direct chain. The indirect target from `0x12f0c` and its initialization/driver binding must be resolved before identifying a playback API or continuous streaming path. The WAV resources do not prove a usable physical audio output.

Required next trace: resolve the function pointer stored at audio state `+8`, then trace its buffer ownership, device queue/DMA descriptor construction, interrupt/completion path, and the initialization that installs the pointer. Do not call `0x1e844` from a custom payload: its ABI and service lifetime have not been established for an injected caller.
