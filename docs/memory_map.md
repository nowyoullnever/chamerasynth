# 메모리 지도

## 오프셋 기반 지도 (확정)

|파일 범위|내용|근거|
|---|---|---|
|`0x000000..0x0001ff`|SPII/SRIy header 및 zero padding|header bytes, vector가 `0x200`에서 시작|
|`0x000200..0x0003ff`|A32 vector/reset/startup/literal pool|A32 instruction stream 및 literals|
|`0x00023c..0x000364`|reset, 초기 MMIO, RAM loop, mode stack 설정|[boot_chain_map.md](boot_chain_map.md)|
|`0x0002dd48…`|bootstrap/application 후보|`0x364` ARM branch target|
|여러 영역|GPZP resource markers (79), JPEG/RIFF embedded data|`0x0629e`, `0x0ffb78`, `0x080340` 등|
|`0x1aee00..0x1fffff`|erased `0xff` tail|byte scan|

## 런타임 주소 후보 (미확정)

|값/범위|상태|근거와 한계|
|---|---|---|
|payload logical base `0x00000000`|유력 가설|vector literal reset `0x3c`와 file `0x23c`가 `file = payload + 0x200`으로 일치한다. BootROM mapping 증거 없음.|
|`0xd0100038`, `0xd0300000..0xd03000c0`, `0xd05001fc`, `0xd07023c0`|MMIO address literal 관찰|reset code가 이 값으로 store한다. peripheral block label은 붙이지 않는다.|
|`0x0010af30..0x001ae74f`|zeroed RAM/BSS 후보|`0x294..0x2dc` loop 값을 end/length로 해석한 결과. register semantics와 base mapping 미확정.|
|stack 영역|미확정|mode별 SP 설정은 확인했으나 derived final SP/address는 확정하지 않았다.|

## SoC 공개 사양과의 관계

Generalplus의 GPCV2247F 제품 페이지는 Arm7TDMI, 4 KiB SRAM 및 64 Mb DDR SDRAM을 열거한다. 이는 시스템에 RAM이 있을 가능성의 외부 단서일 뿐 이 image의 address map을 증명하지 않는다. 공개 page에는 SFR map, DDR controller sequence, pinmux, BootROM API가 없다.

출처: [Generalplus GPCV2247F product page](https://www.generalplus.com/GPCV2247F-rdLSC-phLVNG2jLN5006SVpnSNproduct_detail), 관련 feature page [GPCV2247F](https://www.generalplus.com/GPCV2247F-ta3n6T-phLV3iuZLN5006SVpnSNproduct_detail).

