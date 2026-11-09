# Phase 6 — `0x5025` event producer boundary

Status: **UNRESOLVED**. This report reuses compact Phase 4/5 Ghidra exports restored from result archives. The authorized proprietary image and full Ghidra project were deleted locally; no new disassembly, runtime observation, or device action was performed. File offsets use the unverified hypothesis `file = VA + 0x200`.

## Verified static consumer-to-updater graph

```text
outer loop VA 0x25668
  0x2572c / file 0x2592c : 1f83ffeb  BL 0x63b0        [outer code 0x100]
    0x63f8 / file 0x65f8 : 8e7d00eb  BL 0x25a38       [receive 0x28-byte inner record]
    inner word 0 == 0x5025
      0x6438 / file 0x6638 : 421fa0e3  mov r1,#0x108
      0x6440 / file 0x6640 : 8d2402eb  BL 0x8f67c     [publish outer 0x108]
    0x6488 -> 0x7d10; 0x648c -> 0x6378; return
  0x257b8 / file 0x259b8 : 6ceeffeb  BL 0x21170       [updater]
  branch back to the shared loop
```

| Edge | Evidence | Confidence |
| --- | --- | --- |
| `0x63b0 → 0x25a38` | Retained pseudocode passes `*DAT_00006524`, `&local_24`, `DAT_00006528`, length `0x28` | VERIFIED static call; queue identity unresolved |
| Queue record shape | `0x25984` writes numeric code as first word and copies payload; `0x25a38` returns the word then copies following bytes | STRONGLY INFERRED from decompiler |
| `0x5025 → 0x8f67c(...,0x108)` | Direct instructions above | VERIFIED static edge |
| `0x108 → 0x21170` | Direct outer-loop dispatch above | VERIFIED static edge |

`0x6378` adds an additional publish and `0x25984` message after the observed relay, but its code and queue arguments are unresolved. An immediate replacement of `0x63b0` still skips this cleanup/scheduling path.

## Second `0x5025` consumer

VA `0x1c9c4`, file `0x1cbc4`, receives another 0x28-byte record through `0x25a38(*DAT_0001c988, ..., DAT_0001c984, 0x28)`. Its `0x5025` branch at VA `0x1cafc` publishes `0x108` through `0x8f67c`, updates a state byte, calls `0x1c428`, then returns. It is a second **consumer/relay**, not evidence of a producer.

## Producer conclusion and exact blocker

The producer cannot be identified from retained evidence. The available caller list for `0x25984` does not retain each call's message-code dataflow or prove that its queue argument aliases `DAT_00006524`/`DAT_0001c988`. The archive also lacks queue allocation, ownership, destruction, constant-construction, callback table, and indirect-call targets.

Required next input: an authorized local copy with SHA-256 `720ed0b65c91b149b0916498732b0ecf40227736ef5e3c126c487a7b5253436c` and either the previous Ghidra project or a fresh read-only import. Trace backward from the first `0x25a38` queue argument and each `0x25984` call until a sender whose code field and queue identity both match are proven. Until then, boot/SD/menu/task/power origin must remain unnamed.

Sources: `work/phase6-event/event_producer_boundary.md`, `work/phase5-event/phase5_event_graph.json`, and retained Phase 5 pseudocode.
