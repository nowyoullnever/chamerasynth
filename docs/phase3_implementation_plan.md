# Phase 3 구현 계획 — gate 통과 후에만

1. **Ghidra/identity gate**: appropriate Ghidra environment에서 A32 project를 만들고 task scheduler, state dispatcher, LCD/audio/input/SD functions의 xref와 ABI를 확정한다.
2. **recovery gate**: 별도 recoverable hardware에서 validated read-only backup, restore, update behavior를 기록한다. 현 장치는 대상에서 제외한다.
3. **hook gate**: post-hardware/pre-camera-UI task boundary를 찾아 original bytes, ABI, globals, update independence를 manifest evidence로 고정한다.
4. **tail/layout gate**: resource/header/update bounds와 classified xrefs로 injection region을 검증한다. tail이 탈락하면 non-destructive alternative layout을 재설계한다.
5. **minimal app gate**: only verified stock entry/driver 호출을 쓰는 LCD/input/audio smoke routine을 separate hardware에서 검증한다. synth DSP/UI는 그 다음이다.
6. **updater gate**: original update helper의 erase/write/verify/RAM behavior와 2 MiB behavior를 disassemble + sacrificial readback으로 증명한다. 이 전에는 deployment package를 만들지 않는다.

현재 즉시 작업은 1번의 Ghidra function graph 회수다. Phase 2의 exact next implementation step은 `0x2dd48`, `0x65b0`, `0x21370`, `0x21818` 주변의 A32 project/xref reconstruction이며 firmware patch 작성이 아니다.

