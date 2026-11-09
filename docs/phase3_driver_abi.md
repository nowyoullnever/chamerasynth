# Phase 3 — Driver/API ABI 조사

## 판정

Phase 3에서 **안전하게 호출 가능한 Charmera driver API는 확정하지 못했다.** Ghidra는
display helper와 event dispatcher의 실제 call edge를 제공했지만, UI/input/audio/SD/power에
필요한 structure layout, init predecessor, queue/IRQ ownership, return contract를 완성하지
못했다. 따라서 HAL header, MMIO register definition 또는 stock-call wrapper를 생성하지 않는다.

|기능|정적 chain / 근거|ABI 상태|판정|
|---|---|---|---|
|screen text/draw|`0x21c2c → 0x637ac/0xf0e10/0xf0138/0xf04f4/0x24c9c/0x8f67c`|`r0` context 내부 field와 `r1` meaning, pixel/queue ownership 미확정|후보만|
|button/input|`0x25668 → 0x65b0`, `0x65b0 → 0x25a38` 등|event value encoding, source, polling/IRQ, debounce, caller loop 미확정|미확정|
|audio|Ghidra seed graph에서 callable PCM/DAC/DMA API 미식별|sample format, buffer/DMA/IRQ, init/global 모두 미확정|미확정|
|SD/filesystem|discovery `0x21818` 및 updater `0x21370`의 helper cluster|handle type, file API prototypes, normal app state init 미확정|미확정|
|power/battery|이번 seed graph에 direct API 없음|ADC/GPIO/power state/threshold 미확정|미확정|

## display helper의 reconstructed calling shape

Ghidra는 `0x21c2c`를 no-parameter prototype으로 export했지만, decompiler는 `param_1`,
`param_2`를 사용한다. 이 불일치는 Ghidra type recovery가 아직 완전하지 않다는 증거다.
관찰할 수 있는 것은 다음뿐이다.

- `param_1 + 2`, `+4`의 16-bit field로 pixel/buffer size 같은 값을 계산한다.
- `param_1 + 8`에 allocation-like result를 저장하고 기존 값이 있으면 `0x560`을 호출한다.
- `0x24c9c`에 그 buffer와 `param_2`, constant `2`를 전달한다.
- 끝에 `0x8f67c(*global, param_1 | 0xc0000000)`를 호출한다.

이것은 display work item/bitmap structure일 수 있으나, 사실로 단정할 수 없다. 유효한 ABI로
승격하려면 해당 four caller의 `r0/r1` setup, context allocation/free, queue consumer와
framebuffer/MMIO chain을 모두 추적해야 한다.

## 다음 작업 우선순위

1. `0x25668` caller의 scheduler/task creation과 `0x25a38` event producer를 trace하여
   button event ABI를 복원한다.
2. `0x21c2c` caller 중 하나를 시작점으로 context lifetime과 `0x8f67c` consumer를
   복원한다.
3. `CLICK.WAV`/`BEEP.WAV` string xref에서 PCM buffer, DMA descriptor, IRQ ack까지의
   chain을 찾는다.
4. normal-app file API와 updater-only file API를 분리한다.

그 전에는 device driver 호출을 포함한 synth application 코드를 작성하지 않는다.
