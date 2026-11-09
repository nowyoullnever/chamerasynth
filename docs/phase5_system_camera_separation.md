# Phase 5 system and camera separation

Classifications below are static evidence classifications, not driver/API names.

| VA | Classification | Static evidence | Replacement decision |
| --- | --- | --- | --- |
| `0xcc2c` | Essential system initialization, medium confidence | Initializes global control data and calls `0x8c4a4`, `0x8c604`, `0x8c3dc` through the startup thunk | Preserve |
| `0x1e234` | Audio resource initialization | Opens/stores handles for CLICK, POWERON, POWEROFF, BEEP, IMG WAV resources | Preserve until a tested replacement lifecycle exists |
| `0x6134` | Mixed startup UI/media/service initialization | Startup state, POWER_ON_LOGO.JPG, and `0x1e844(2)` playback request occur in same path | Do not remove as camera-only |
| `0x2d31c` | Unknown backend/service initialization | Object acquisition plus indirect callbacks at object offsets `+4` and `+0xc` | Preserve; callback targets unresolved |
| `0x25a38`, `0x25984`, `0x8f67c` | Event queue and scheduling | Receiver, sender, and outer event publisher on proven update relay | Preserve |
| `0x7d10`, `0x6578` | Cleanup/task transition, unknown details | Executed after `0x5025` relay before handler returns | Preserve |
| `0x21dc8`, `0x21d20` | Shared state/UI candidates | Reached from multiple internal-event branches | Not camera-only proof; preserve |
| `0x1cbc4` | Camera/video-state candidate, low confidence for exclusivity | Large state machine handles `0x500d..0x5014`, `0x7000`, and also relays `0x5025 → 0x108` | Not a safe hook |

The camera application has not been separated into a safely removable region. The evidence instead separates a narrow set of confirmed shared event/update services from mixed or unknown startup code. A camera-facing resource string or state event is insufficient proof that its containing routine is independent of system initialization.

The minimum preservation boundary is: outer loop `0x25668`, queue publisher/receiver/sender, startup service calls from `0x63b0`, `0x5025` relay, post-loop cleanup, and outer `0x108 → 0x21170` dispatch. Power management has not been independently identified in this chain and remains unknown.
