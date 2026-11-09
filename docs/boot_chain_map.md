# 부트 체인 지도

## 확인된 체인과 공백

```text
[미확인 SoC BootROM]
          │  (SPI boot / SPII header 해석은 추론)
          ▼
flash offset 0x000000: SPII/SRIy header
          │
          ▼
offset 0x000200: A32 exception vectors
          ▼
offset 0x00023c: reset startup, CPSR=0xd3, early MMIO writes
          ▼
offset 0x000294: copy/zero loop 후보, mode별 stack 설정
          ▼
offset 0x000364: branch → 0x0002dd48
          ▼
bootstrap/application 후보 (정확한 main 미확정)
```

## 단계별 근거

|단계|상태|근거|설명|
|---|---|---|---|
|BootROM|미확정|`SPII` at `0x0`, official GPCV2247F page의 SPI flash/XIP feature|ROM boot source, SPI mode, header validation, recovery 진입법은 공개 근거 없음|
|flash header|관찰|`SPII` `0x0`, `SRIy` `0x14`, file size `0x8`|container이 존재한다. field 의미는 모름|
|첫 실행 코드|관찰|A32 vectors `0x200`, reset `0x23c`|header 이후 vector payload가 있다|
|clock/DDR|부분 관찰|early stores `0x24c..0x290` to `0xd0…` literals|MMIO writes만 확인. 어떤 write가 clock/DDR인지, 값의 의미는 미확정|
|RAM init|추론|loop `0x294..0x2dc`, values `0x10af30`/`0xa3820`|BSS zeroing 또는 data init 가능성. runtime mapping과 range 재검증 필요|
|stack/interrupt init|관찰|CPSR mode changes `0x2e0+`|mode별 SP를 설정한다. vector relocation/VIC 초기화는 미확정|
|application 진입|후보|branch `0x364 → 0x2dd48`|bootstrap/main 후보. call graph와 decompilation 필요|

## 임시 보존/교체 판단

|구성요소|Phase 2 전 판단|
|---|---|
|BootROM|보존 강제. ROM image와 recovery contract를 모른다.|
|SPII header 및 초기 vector/startup|보존 후보. 이해 없이 대체 금지.|
|clock/DDR/MMIO 초기화|보존 후보. register map/panel/DRAM 설정 미확정.|
|application state/UI|향후 교체 후보. 단, LCD/input/audio/storage HAL이 확인된 뒤에 한한다.|
|리소스/카메라 app|신스 목표에는 교체 가능성이 높지만, flash layout 및 updater 의존성 분석 전 삭제/재배치는 금지.|

## 다음 검증

1. 파일 `0x0` header와 payload mapping을 GPCV2247F 전용 packer/ROM 자료 또는 다른 동일 board dump로 상호검증한다.
2. `0x23c..0x364`, `0x2dd48`를 correct ARM A32 base 후보로 Ghidra에 수동 import하여 literals, callers, copy loops를 확인한다.
3. UART boot log 또는 비파괴 SPI readback이 가능한 별도 희생 장비가 확보될 때만 BootROM 가설을 검증한다.

