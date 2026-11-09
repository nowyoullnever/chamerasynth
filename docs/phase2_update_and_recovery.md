# Phase 2: Updater와 recovery 분석

## 직접 관찰한 updater 후보

|범위/오프셋|관찰|결론|
|---|---|---|
|`0x21370..0x21814`|시작 `f0 4f 2d e9`, `sub sp,#0x5c`; `0x213a4→0x30d54`, `0x213c8→0x211fc`, `0x2144c..0x2150c` byte loop, `0x21594` block loop|updater main 후보. erase/write helper semantics은 미확정|
|`0x21818..0x218a4`|`push {r4,lr}`/`pop {r4,pc}`; `0x2183c`→`C:\\JH_` (`0x218ac`), `0x21848`→`5408`, `0x21854`→`*.bin`, `0x21884`→`202505201029`; calls `0x908b8`,`0x470`,`0x51c`,`0xe2ef0`,`0xe2e54`,`0x4b4`|filename discovery/timestamp comparison pipeline의 강한 후보. helper names/semantics 미확정|
|`0x217b4`|`E28A0B40` (`ADD r0,r10,#0xb40`), `EBFF8158` (`BL 0x1d20`)|KCP가 주장한 erase 지점이지만, 이 bytes만으로 SPI erase라고 증명할 수 없음|

KCP stock/super/webcam 2 MiB image와 Sirius image의 `0x21370..0x218a4`는 동일하다. 따라서 KCP의 해당 code-offset 참조가 **같은 bytes**를 가리킨다는 사실만 전이된다. 그 코드에 대한 KCP 설명은 원본 helper disassembly 없이 사실로 전이되지 않는다.

## 질문별 판정

|질문|판정|
|---|---|
|file discovery|후보 확인: path/pattern strings와 candidate function 존재|
|timestamp parsing|후보 확인: stock timestamp string/direct call pipeline 존재|
|byte-sum checksum|byte loop 존재, checksum algorithm/compare target 미확정|
|flash erase/write/verify range|미확정|
|post-update erase|미확정; `0x217b4`는 erase 확증 아님|
|updater RAM/SPI execution|미확정|
|updater overwrite|미확정|
|hook이 update mode를 막는지|미확정; hook 자체가 없음|
|failed app recovery|보장 불가|
|2 MiB wrap / 30 block|KCP 산술 가설만 존재. 원본 SPI helper와 physical chip addressing 검증 전 사용 금지|

SD update package는 생성하지 않는다. filename/checksum 형식은 installation safety 또는 rollback 보증이 아니다.

