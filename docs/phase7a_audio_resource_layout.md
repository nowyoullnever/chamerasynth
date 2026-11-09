# Phase 7A — stock audio-resource layout

## Status and source identity

This is offline static analysis only. The analyzed local source is 2,097,152 bytes with SHA-256 `720ed0b65c91b149b0916498732b0ecf40227736ef5e3c126c487a7b5253436c`. The source image, extracted WAV, and modified candidate are ignored locally and are not repository artifacts.

## Recovered resource index

Ghidra export `work/phase7a/ghidra_exports/pseudocode/00197c.c` shows that `0x177c` reads a resource index from the nonvolatile resource base represented by `DAT_00120000`, allocates 0x20-byte runtime records, and copies 0x18-byte on-image entries. The generated reader at `0x133c` uses each entry's `+0x14` field as a sector start; the next entry's start determines the sector allocation. This is a static dataflow result, not a runtime trace.

The matching bytes in the supplied source form a table at file `0x120000`: header count `0x2b` (43), entries beginning at `0x120018`, each 0x18 bytes, and a 0x200-byte sector unit. The table uses names without dots, which matches the lookup behavior in `0x1298`: the input dot is skipped while comparing up to 0x28 bytes.

| Resource | Index | Entry file offset | Start sector | Next start sector | Resource start | Allocation |
|---|---:|---:|---:|---:|---:|---:|
| `BEEPWAV` | 4 | `0x120078` | `0x0f` | `0x17` | `0x121e00` | `0x1000` |
| `CLICKWAV` | 6 | `0x1200a8` | `0x19` | `0x1d` | `0x123200` | `0x0800` |
| `IMGWAV` | 25 | `0x120270` | `0x1fe` | `0x209` | `0x15fc00` | `0x1600` |
| `POWEROFF_AUDIOWAV` | 29 | `0x1202d0` | `0x212` | `0x223` | `0x162400` | `0x2200` |
| `POWERON_AUDIOWAV` | 30 | `0x1202e8` | `0x223` | `0x22f` | `0x164600` | `0x1800` |

The available evidence supports an embedded, sector-addressed resource partition, not a generic external file container. No field has been proven to be a checksum, signature, encryption tag, or update metadata.

## Exact BEEP.WAV allocation

`BEEPWAV` has a proven allocation from source file `0x121e00` through exclusive end `0x122e00` (4,096 bytes, 0x200-byte aligned). Its RIFF/WAVE container occupies `0x121e00..0x122deb` inclusive (4,076 bytes): PCM format 1, mono, 11,025 Hz, 16-bit, block alignment 2, and data length 4,032. The remaining 20 allocation bytes are all `0xff`.

The original BEEP container SHA-256 is `ca9717d719bb55d2b8bef5debb90b99589f2a37f97c8f7c7aa4df765bb718206`. The full allocation SHA-256 is `cc8744164fb097823a6f3b53b0ede632ff525a0b63c8941a83af0e8c6c821ddb`.

`0x1e234` resolves `BEEP.WAV` and stores its 16-bit resource handle at runtime table offset `+0x0c`; `0x1e844(5)` reads that slot. This is the recovered stock selector mapping. It does not prove which physical button, if any, invokes selector 5.

## Reproducible offline tool

`tools/phase7a_resource_tool.py` verifies source identity before every operation.

```powershell
python tools/phase7a_resource_tool.py inspect references/Project-Sirius/Original_Firmware.bin work/phase7a/beep_layout.json
python tools/phase7a_resource_tool.py tone references/Project-Sirius/Original_Firmware.bin work/phase7a/BEEP_low_amplitude.wav
python tools/phase7a_resource_tool.py manifest references/Project-Sirius/Original_Firmware.bin work/phase7a/BEEP_low_amplitude.wav work/phase7a/beep_replacement_manifest.json
python tools/phase7a_resource_tool.py apply references/Project-Sirius/Original_Firmware.bin work/phase7a/beep_replacement_manifest.json work/phase7a/BEEP_low_amplitude.wav work/phase7a/Original_Firmware_beep_candidate.bin work/phase7a/beep_candidate_validation.json
```

The generated tone is deliberately low amplitude, PCM-format-compatible, and exactly 4,076 bytes. `apply` rejects another source hash, a different length or format, unaligned placement, metadata writes, and any changed byte outside the declared BEEP container. It also proves byte-for-byte restoration in memory. Its output is an ignored local `analysis-only-copy`, never an update package.

Observed validation: candidate SHA-256 `818f489919c070bccf8d45dc0d95685ad3737dd31ca0b032b6f5f598d2217534`; 3,992 bytes differ only within `0x121e00..0x122deb`; restoration returned the exact original source bytes.

## Remaining unknowns

The table and allocation do not establish device boot behavior, update acceptance, a resource checksum/signature, a decoder's full error handling, or actual sound output. No source byte was changed during analysis.
