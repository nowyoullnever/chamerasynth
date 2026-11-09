# Phase 6 — application integration decision

## Result

No safe binary hook was established. The preferred Phase 6 integration is a **host-side application contract only**; it preserves the modeled update relay and does not modify the stock image.

| Design | Evidence | Decision |
| --- | --- | --- |
| A. UI callback replacement | `0x6134` mixes startup wait, `POWER_ON_LOGO.JPG`, audio request `0x1e844(2)`, and event publication. It is not a menu-only callback. | Not approved |
| B. Custom application state | `0x2d31c` performs indirect calls through object `+4` and `+0xc`; target ownership and ABI are absent. | Not approved |
| C. Application wrapper | Inner queue ownership, other message semantics, termination, `0x6378` cleanup, and `0x5025` producer are unresolved. | Not approved |

The old candidate `VA 0x2572c`, file `0x2592c`, bytes `1f83ffeb`, remains protected. It calls the handler that owns the verified relay; replacing it would need the unknown 0x28-byte message ABI, all startup/cleanup effects, correct return behavior, and a safe executable payload location.

## Implemented offline design

The Phase 6 host integration skeleton intentionally has no stock addresses or MMIO. It models a synth application as an event participant and delegates `0x5025` to the update relay before application shutdown/return. Its mock audio interface has explicit buffer ownership and start/stop/release lifecycle. This establishes a testable design contract only; it is neither a stock-handler replacement nor an ARM injection implementation.

## Updater reachability

The proposed host model preserves updater reachability only when the inner `0x5025` is delivered. It must not synthesize that event, name its source, or prove physical update recovery. The actual firmware path remains the verified static fragment `0x63b0 → 0x8f67c(...,0x108) → 0x21170`.

## Smallest unresolved issue

Recover one concrete camera-only callback/state registration with target address, caller ABI, global ownership, message ownership, return contract, and proof that it does not bypass the `0x5025` relay and cleanup. A separately verified executable/writable payload location is also required before an ARM hook can exist.
