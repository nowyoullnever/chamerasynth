# Phase 5 hook and injection decision

## Decision

No stock-image hook or injection region is approved. No firmware patch was created.

The Phase 4 candidate `VA 0x2572c`, file `0x2592c`, original bytes `1f83ffeb` (`BL 0x63b0`) is explicitly rejected for replacement. It is not an isolated camera UI launch: removing it suppresses the observed inner `0x5025 → outer 0x108 → 0x21170` lifecycle and skips startup/cleanup work.

| Option | Evidence result | Decision |
| --- | --- | --- |
| A: replace camera UI state | No isolated menu-state transition recovered | Not approved |
| B: redirect UI callback | `0x2d31c` uses indirect callbacks, but target, ABI, ownership, and UI-only status are unresolved | Not approved |
| C: wrapper around stock handler | `0x63b0` has an internal receive loop and conditional exit; calling it then a synth has no demonstrated return contract | Not approved |
| Design-only relay model | `0x5025` can be relayed in the host model | Not firmware implementation |

For the rejected `0x2572c` site, the only recoverable calling context is direct outer-loop dispatch. A compatible replacement would need the A32 call ABI, preserve the caller's stack/register expectations, preserve all startup globals/queues, consume the unknown 0x28-byte internal message ABI, propagate `0x5025`, execute cleanup, and return at the original lifecycle point. Those requirements are not recovered; no fabricated routine is supplied.

## Tail and layout audit

`tools/audit_tail_layout.py` audits the 26 exported direct Ghidra references into file tail `0x1aee00..0x1fffff`. All inspected target bytes are `FF`, but references are `DATA`/`PARAM` hypotheses and include reads/writes such as `ldr`, `str`, `mov`, and `add`. They do not prove executable addressability, ownership, erase behavior, or absence of computed references.

The header word at file `0x10` is little-endian `0x001b0000`, but this audit found no code-reference semantics that establish it as an image length or partition boundary. Large FF runs and candidate smaller runs are therefore not code caves. The manifest remains `analysis-only`; its tail note records this audit and no patch entry exists.

The existing relocatable ARM prototype remains an offline artifact only. A new integration ELF was not justified because no safe hook contract or executable region was established.

## Update compatibility boundary

Phase 4 updater code remains preserved as analysis evidence only. This phase did not establish complete transfer length, 64 KiB erase extent, 256-byte program/verify behavior, post-update erase behavior, RAM execution, overflow/wraparound, or reboot recovery. No package, patch image, SD artifact, USB/vendor command, or flash operation was produced.

## Exact gate before patching

Establish one UI-only callback/state target with: executable file-to-runtime mapping, caller ABI, stack/global dependencies, event ownership, return behavior, and proof that `0x5025` production/relay plus updater cleanup remain reachable. Independently establish a writable/executable insertion region and updater image-length/erase rules. Both gates are required.
