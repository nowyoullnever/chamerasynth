/*
 * Offline A32 object only.  It is not linked, injected, packaged, or proven
 * callable by Charmera firmware.  It makes no MMIO access and calls no stock
 * firmware function.  The external hook ABI is deliberately unresolved.
 */
.syntax unified
.arm
.section .text.synth_stub, "ax", %progbits
.align 2
.global synth_entry
.type synth_entry, %function
synth_entry:
    push    {r4, lr}
    bl      2f
1:
    bl      3f
    b       1b
.size synth_entry, .-synth_entry

2:  /* synth_app_init: TODO: call stock init only after ABI is verified. */
    /* TODO: only call a stock initializer after entry ABI is verified. */
    mov     r0, #0
    bx      lr

3:  /* synth_app_tick: button/LCD/audio/power operations are unresolved. */
    /* TODO: button, LCD, audio, power, and reset operations are unresolved. */
    mov     r0, #0
    bx      lr

