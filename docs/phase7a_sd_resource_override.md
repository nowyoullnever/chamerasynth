# Phase 7A — SD resource override assessment

## Verdict

No stock SD-card resource override path, directory, filename, precedence rule, or fallback behavior is proven. Do not place `BEEP.WAV`, `BEEPWAV`, a JH file, or any modified image on a camera microSD card.

## Evidence boundary

The recovered stock resource resolver is the `0x1298 → 0x1310` path. Ghidra output from `0x177c`, `0x133c`, `0x1520`, and `0x16e4` shows a table-derived sector start and reads from the embedded resource base `DAT_00120000` in 0x200-byte units. The initialization at `0x1e234` resolves names into runtime handles; playback selects those handles through `0x1e844`.

This trace establishes only the embedded resource route. It contains no demonstrated FAT/exFAT path traversal, external resource filename construction, SD mount lookup, or branch that prefers removable media over the embedded table. The independently recovered updater/SD-discovery code from Phase 4 is not evidence that this audio resolver honors SD files.

## Exact remaining requirements before an SD claim

1. Static caller-to-callee evidence from a confirmed SD mount/open API into the resource resolver, including a specific path/name buffer.
2. A proven precedence/fallback condition between SD and embedded sectors.
3. Proof of file format, length limit, allocation, validation, and error return behavior for the SD-loaded resource.
4. A separate recovery-qualified device test plan. A stock restore file alone does not establish that the updater remains reachable after a failed boot.

Until all four exist, the only defensible statement is that an SD override is unproven.
