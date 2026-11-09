# Phase 4 — 최소 display/input/audio interface

## 공통 판정

실제 hardware-compatible callable API는 아직 없다. 아래는 code-level call/argument evidence이며,
global ownership, task context, completion, board connection이 확인될 때까지 synth driver wrapper를
작성하지 않는다.

|영역|최소 후보|확인된 입력/상태|미확정 항목|판정|
|---|---|---|---|---|
|display|string draw VA `0x21a2c`, file `0x21c2c`|context `r0`, payload `r1`; ctx `+2/+4/+8`; allocation/raster/submit chain|ctx lifetime, queue completion, pixel format, `0x8f67c` meaning|호출 금지|
|button/event|receive `0x25a38`, send `0x25984`, camera handler `0x63b0`|32-bit event code + payload; receive max `0x28` in this handler|physical GPIO/IRQ producer, code-to-button map|queue ABI만 후보|
|audio|WAV resource init `0x1e234`, file `0x1e434`|`CLICK.WAV`, `POWERON`, `POWEROFF`, `BEEP`, `IMG` handle initialization|PCM/DAC/PWM/DMA/IRQ/play call and PCB output|미확정|

## display

`0x21a2c` entry head: `70402de90040a0e1080090e518d04de2`. Callers are VA `0x985c`,
`0x1b8dc`, `0x1b968`, `0x1d380`. It checks `ctx+8`, allocates through `0x637ac`, invokes
`0xf0e10/0xf0138/0xf04f4`, calls `0x24c9c(buffer,r1,2)`, then calls
`0x8f67c(*global, ctx | 0x0c000000)`.

For example caller VA `0x985c` (file `0x9a5c`) sets context geometry/position fields including
`+0xc=100`, `+0xe=0xd2`, `+4=0x15` before the call. This supports a context-backed draw work item
inference, not an API declaration. The buffer is allocated into `ctx+8`; neither release site nor
completion consumer is known.

## buttons and event messages

`0x25a38` has `(queue_context, out_event_word, payload_destination, requested_length)` shape.
`0x25984` has `(queue_context, event_word, payload_source, payload_length, mode)` shape and uses a
lock-like pair plus `0x8f67c/0x8f73c`. This is sufficient to correct the numeric event type in
`0x63b0`; it is not enough to call the queue from a new task.

No static chain connects a particular physical button GPIO/IRQ to the `0x100` outer event or to a
specific inner code. A first button API is therefore not yet available.

## audio

`0x1e234` is called by `0x63b0` and uses resource helper `0x1310` for the listed WAV assets; it
stores 16-bit handle-like values in a global structure whose literal is file `0x1e490 = 0x00110284`.
This is asset initialization, not playback. The `SoundHandler` string at VA `0xb438c` / file
`0xb458c` belongs to AVI `VideoHandler/SoundHandler/DataHandler` metadata formatting and is not an
audio output driver.

No path from a WAV handle to PCM buffer, DAC/PWM register, DMA descriptor, or audio IRQ was recovered.
The SoC may advertise audio capabilities, but actual Charmera PCB audio connection remains unknown.
