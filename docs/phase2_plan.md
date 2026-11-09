# Phase 2 계획 (자동 진행 금지)

## 목표

카메라 app을 보존하는 것이 아니라, 검증된 최소 hardware abstraction 위에서 standalone synth를 설계할 수 있는지 판단한다. 이 문서는 Phase 1 이후의 **제안**이며 어떤 device 작업을 승인하지 않는다.

## Gate 순서

1. **식별 gate** — camera board revision, SoC marking, flash part/capacity, LCD/audio connection을 사진·문서로 확인한다. GPCV2247F/1235F 가정을 분리한다.
2. **복구 gate** — 별도 희생 장치에서 repeatable read-only SPI backup 두 개 이상을 hash compare하고, validated restore procedure를 만든다. 현재 대상은 opening 불가이므로 통과 불가다.
3. **정적 boot gate** — SPII header field, payload base, reset `0x23c`, bootstrap `0x2dd48`, RAM/DDR sequence를 correct ARM A32 import로 재구성한다.
4. **HAL discovery gate** — LCD, buttons, audio DAC/DMA, SD, power를 하나씩 증거 표에 승격한다. register/value 추측 source 작성 금지.
5. **safe execution gate** — SD updater가 아닌, proven temporary loader/ROM contract가 있을 때만 RAM-resident diagnostic을 별도 장치에서 고려한다. 없으면 외부 programmer/recovery path 확보가 선행된다.
6. **synth architecture gate** — mono PCM voice engine, event queue, display UI, preset/sample storage의 memory/latency budget을 실제 RAM/DMA 근거로 작성한다.

## Phase 2 산출물 후보

- Ghidra project/import notes와 address/offset transform 문서
- annotated boot/startup call graph
- evidence-backed LCD/input/audio/SD HAL headers (register definitions은 확인 후에만)
- host-only DSP prototype 및 golden PCM tests
- recovery checklist와 sacrificial-device test log

## 금지 항목 유지

- 이 원본을 포함한 flash image 또는 JH_5408 update package 생성/배포
- KCP/ZTKVR의 register value, startup code, patch offset을 Charmera 사실로 복사
- 현재 대상에 vendor command, update, USB flashing, SPI erase/write 수행

