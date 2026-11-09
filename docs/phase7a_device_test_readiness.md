# Phase 7A — device-test readiness

## Decision: NO-GO for physical installation

The first useful future device experiment remains Test A: an equal-size BEEP resource replacement that retains stock control flow. Phase 7A proved the embedded resource index, BEEP allocation, RIFF/WAVE format, alignment, and offline diff/restoration boundary. It did not prove update acceptance or external recovery. Therefore no microSD installation, USB command, flash operation, or device connection is authorized from this result.

## Test A readiness

| Gate | State |
|---|---|
| Exact original source identity | Verified |
| BEEP resource ID, allocation and format | Verified statically |
| Equal-size low-amplitude replacement | Host-generated and format-validated |
| Changed-byte range and restoration | Host-validated |
| Resource checksum/signature rule | Unresolved |
| SD update container and acceptance | Unresolved |
| External recovery method demonstrated on comparable hardware | Unresolved |
| Physical install authorization | Not granted in this phase |

Required before any later Phase 7 physical review: demonstrate a board-compatible external recovery method (for example, identified SPI access with a compatible programmer and verified read/restore procedure), preserve a separately hash-verified stock source, determine the actual updater input/container and its validation, use a sacrificial device with stable power, and obtain explicit authorization for that single installation attempt.

A restore file does not itself make recovery safe. A failed boot can prevent the normal SD updater from running; without an external recovery route, the camera can remain unusable.

## Test B and Test C

Test B remains NO-GO. The stock selector is now clearer: selector 5 reads the BEEP handle, selector 0 reads CLICK, and selector 2 reads POWERON. But no physical button producer, GPIO/IRQ mapping, UI-event contract, or safe hook has been recovered.

Test C remains NO-GO. The request service reaches `0x12f0c → 0x133f0 → *(state + 8)`, but the PCM backend ABI, DMA/DAC/PWM route, buffer completion, and continuous playback ownership remain unresolved. The Phase 6 sine generator stays host-only.
