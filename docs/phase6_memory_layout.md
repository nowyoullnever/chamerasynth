# Phase 6 — executable memory and updater boundary

No executable injection region is approved.

## Tail reference classification

The retained Phase 5 audit enumerates 26 direct Ghidra references into `file 0x1aee00..0x1fffff`. Every checked target byte was `FF`, but the references are analyzer `DATA`/`PARAM` interpretations of `ldrb`, `ldr`, `str`, `mov`, or `add`. This includes writes and numeric-address candidates; none proves unused executable storage.

| Target groups | Reference count | Classification |
| --- | ---: | --- |
| `0x1ff7e2`, `0x1c2000`, `0x1c0000`, `0x1fd880`, `0x1e8480`, `0x1f2102` | 11 | PARAM/data-address candidates; mapping/meaning unresolved |
| `0x1da2c0/0x1da2c1` | 10 | Mixed load/store references; cannot overwrite |
| `0x1dbc2e`, `0x1df100` | 3 | Explicit data/write candidates; cannot overwrite |
| all above | 26 | No executable ownership, computed-xref coverage, or update preservation proof |

The header word at file `0x10` equals `0x001b0000` little-endian. The retained audit found no semantic code reference establishing image length, load map, or partition boundary. It remains **UNRESOLVED**.

## Update boundary

Retained updater evidence has 64 KiB erase (`0xd8`), 256-byte program (`0x02`) and verify read (`0x03`) operations. Its post-update path can request erase at progress plus `0x10000`; no proof establishes physical 2 MiB decode, address wrap behavior, RAM relocation, post-update extra erases, or reboot recovery. Existing third-party tooling that truncates at `0x1e0000` is not a valid packaging or preservation mechanism.

Consequently the manifest remains `analysis-only`, every tail reference remains protected by policy, and no patched image or installation package is produced. Required next proof is an authorized source image plus startup/load and updater length/erase dataflow analysis.
