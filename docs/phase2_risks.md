# Phase 2 위험 목록

|위험|현재 근거|제어|
|---|---|---|
|boot-critical hook|`0x2dd48`은 reset의 branch destination이며 hook 안전성 미확정|모든 hook patch 금지|
|tail overwrite|tail은 FF지만 header/resource/computed reference 가능성 미제거|`unverified` region, output hard-fail|
|wrong SoC/board assumptions|GPCV2247F, GPCV1235F/CBB3, GPL326XXB 간 동일성 미입증|register/driver/pin value 이식 금지|
|updater self-destruction|erase/write ranges 및 RAM execution 미확정|JH package/SD write 금지|
|recovery 부재|현재 장치는 open/backup/external recovery 불가|physical installation Phase 2에서 금지|
|ABI/global-state corruption|candidate function prototypes/task context 미확정|stock function 호출/branch injection 금지|
|false disassembly|raw data를 A32로 해석할 수 있음|instruction은 branch/function-boundary/xref로 교차확인; Ghidra import 필요|
|host-only success 오해|LLVM object assembly만 통과|host build를 hardware function proof로 사용 금지|

## emulation 한계

Unicorn은 설치되어 있지 않고, 설치하지 않았다. ARM emulation이 가능해도 BootROM, SPI mapping, DDR timing, MMIO peripheral, LCD/audio DMA, SD card, power behavior를 제공하지 않으면 boot/hardware를 검증하지 못한다. 현재 테스트는 branch codec, source immutability, manifest gates, patch restoration, local object disassembly까지만 다룬다.

