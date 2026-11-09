/*
 * Offline-only ABI prototype for the observed camera-state call site:
 *   shared event loop VA 0x2572c calls handler VA 0x63b0 with r0 pointing
 *   at caller-owned event-loop stack storage.
 *
 * This file is deliberately not linked into, injected into, or packaged with
 * firmware. It performs no MMIO, makes no stock call, does not dereference or
 * retain r0, and returns immediately with the caller's volatile registers
 * unchanged. A hardware-compatible replacement needs the unresolved state,
 * display, input, audio, and insertion-layout contracts documented in Phase 4.
 */
.syntax unified
.arm
.section .text.synth_event_handler, "ax", %progbits
.align 2
.global synth_entry
.global synth_camera_event_handler
.type synth_entry, %function
.type synth_camera_event_handler, %function

synth_entry:
    b       synth_camera_event_handler

synth_camera_event_handler:
    bx      lr

.size synth_entry, synth_camera_event_handler - synth_entry
.size synth_camera_event_handler, .-synth_camera_event_handler
