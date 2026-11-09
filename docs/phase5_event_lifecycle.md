# Phase 5 event lifecycle

Status: partially traced by offline static analysis. `file offset = logical VA + 0x200` is a mapping hypothesis, not a runtime mapping proof.

## Observed ordered path

```text
VA 0x25668 outer loop
  0x25674: r1 = 0x100
  0x2567c: BL 0x8f67c                 (publish initial outer event)
  receive outer event
  0x2572c: BL 0x63b0                 (when event is 0x100)
    0x63bc: call/thunk to 0xcc2c
    0x63c0: call 0x1e234
    0x63c4: call 0x6134
    0x63d0: call 0x2d31c(0xf8500000)
    0x63f8: BL 0x25a38               (receive internal queue message)
    internal code 0x5025:
      0x6438: r1 = 0x108
      0x6440: BL 0x8f67c             (publish outer updater event)
      leave internal-loop termination path
    0x6488: BL 0x7d10
    0x648c: BL 0x6578
    return to outer loop
  0x257b8: BL 0x21170                (when outer event is 0x108)
  0x257bc: B 0x2569c                (resume outer loop)
```

Relevant original bytes: `0x2572c`/file `0x2592c` = `1f83ffeb`; `0x257b8`/file `0x259b8` = `6ceeffeb`; `0x6438`/file `0x6638` = `421fa0e3`; `0x6440`/file `0x6640` = `8d2402eb`.

## What is and is not proven

| Question | Result | Evidence boundary |
| --- | --- | --- |
| `0x100 → 0x63b0` | Proven static control flow | Outer loop instructions and direct call |
| `0x5025 → outer 0x108` | Proven static control flow | `0x6438/0x6440` in `0x63b0` |
| `0x108 → 0x21170` | Proven static control flow | Outer switch call at `0x257b8` |
| Producer of `0x5025` | Unresolved | No sender/caller was tied to the internal queue and condition |
| Physical/software condition | Unresolved | Event value alone cannot identify SD/update/user condition |
| `0x5025` means update request | Strong inference, not named proof | Its observed relay reaches updater; a second consumer at `0x1c9c4` also relays `0x108` |
| Full updater lifecycle | Unresolved | Discovery/flash execution order and runtime queue identities remain unproved |

The direct literal `0x00005025` was not found in the raw image. Its construction may be instruction-immediate or arithmetic; this does not identify a producer.

## Queue and exit state

`0x8f67c` is the observed outer-event publisher. The outer loop passes a queue-like handle at its context `+0x10`; its exact type and global allocation site are not recovered. `0x25a38` receives a 0x28-byte internal message in `0x63b0`; `0x25984` is the paired observed internal-message sender. Ghidra global pointer candidates feeding these calls include `DAT_00006518`, `DAT_00006520`, and `DAT_00006524`; their concrete runtime addresses and ownership are not proven.

On the observed `0x5025` branch, `0x63b0` publishes `0x108`, takes an internal-loop termination value, then executes `0x7d10` and `0x6578` before return. These calls are cleanup/scheduling candidates, not removable no-ops.

## Integration consequences

An immediate return at `0x2572c` skips startup calls, internal message consumption, the demonstrated `0x5025 → 0x108` relay, and post-loop calls. It makes updater reachability fail in the supplied logical model.

A handler that never returns prevents the synchronous outer loop from receiving its queued `0x108` in this model. Actual firmware scheduling may add concurrency; static analysis does not prove a hardware timing result.

`tools/event_lifecycle_model.py` and `tests/test_event_lifecycle_model.py` model only this observed slice. They compare stock relay, rejected empty replacement, and a design-only relay model. They do not emulate firmware, queues, updater, or hardware.

## Required next trace

Recover the producer that sends internal code `0x5025` to the queue read at `0x63f8`, including message payload, sender context, preceding state transition, and its relation to update discovery at VA `0x21618`. Until then, a replacement of `0x63b0` or `0x2572c` is not justified.
