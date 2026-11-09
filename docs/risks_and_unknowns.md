# 위험과 미지점

|위험/미지점|영향|현재 상태|Phase 2 전 해소 방법|
|---|---|---|---|
|SPI dump의 provenance·완전성|잘못된 image를 기준으로 boot/flash layout을 설계할 수 있음|2 MiB dump와는 일치, 확정 아님|동일 장치의 read-only 반복 dump와 hash 비교, board/flash identity 기록|
|BootROM/SPII header 계약|부팅 불능/brick|미확정|전용 datasheet/packer/ROM 정보 또는 희생 장치의 비파괴 boot log|
|clock/DDR init|부팅 직후 hang|MMIO store만 관찰|A32 decompile + correct SFR map; 값 이식 금지|
|register/pin/IRQ map|LCD/input/audio/SD 오동작|미확정|hardware schematic 또는 dynamic trace/logic capture를 별도 장치에서 수행|
|GPCV2247F vs GPCV1235F/CBB3 혼동|잘못된 binary·register 적용|KCP가 1235F라고 주장, Sirius path는 `2247`; 동일성 없음|device marking/board revision과 vendor docs로 확정|
|ZTKVR GPL326XXB 이식|즉시 오동작|비호환|analysis pattern만 참고, SFR/초기화/driver copy 금지|
|SD updater의 range/wrap|updater block 또는 boot-critical block erase|KCP의 30-block 방식은 미검증, non-FF tail truncation 결함|원본 updater full disassembly와 sacrificial hardware readback 전에는 사용 금지|
|복구 수단 없음|단일 장치 영구 손상|사용자는 housing/open SPI backup/recovery connection 불가|Phase 2 flashing을 시작하지 않는다; first create verified restore path on separate hardware|
|license/proprietary firmware|공개 저장소 유출|원본 bin은 proprietary|`.gitignore` 유지, derived reports만 commit, binary 재배포 권리 확인|

## 중단 조건

다음 중 하나라도 충족되지 않으면 flash-ready firmware나 SD update package를 만들지 않는다.

- exact SoC/flash chip/board revision 확인
- verified, repeatable, read-only backup 및 restore procedure
- BootROM/header/startup/DDR contract의 증거
- updater erase/write/verify 범위의 disassembly와 별도 장치 검증
- LCD/button/audio 최소 HAL의 register-level 증거

