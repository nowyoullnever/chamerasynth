# Phase 3 — Ghidra A32 분석 기록

## 실행 사실

**Ghidra를 실제 실행했다.** Ghidra 12.2와 Temurin JDK 25로 headless import와
decompiler export를 완료했다. 입력은 원본에서 새로 만든 payload 복사본뿐이며 원본은
읽기 전용으로 SHA-256을 확인했다.

|항목|값|
|---|---|
|원본|`references/Project-Sirius/Original_Firmware.bin`|
|원본 크기 / SHA-256|`0x200000` / `720ed0b65c91b149b0916498732b0ecf40227736ef5e3c126c487a7b5253436c`|
|분석 입력|원본 file `0x200..0x1fffff`의 새 payload 복사본 (`0x1ffe00` bytes)|
|payload SHA-256|`36c1743ecf8fb8dc26980304f3cc8e686dccf4588941a33e9341c85f5155261a`|
|loader / language|Raw Binary / `ARM:LE:32:v4t:default`|
|논리 load address|`0x00000000`|
|산출물|`work/ghidra/projects/CharmeraA32`, `work/ghidra/exports/function_graph.json`, `work/ghidra/exports/pseudocode/`|

Ghidra에 넣은 주소 변환은 `file offset = logical VA + 0x200`이다. vector의
reset literal `0x3c`와 file `0x23c`가 맞는다는 관찰에 기반한 가설이며, BootROM의
SPI mapping 또는 실제 runtime VA 증명은 아니다.

## 재현 절차

`tools/prepare_ghidra_payload.py`는 원본 크기와 SHA-256을 먼저 확인한 뒤 새
payload/metadata만 쓴다. `tools/run_ghidra_analysis.ps1`은 다음 조건으로
분석한다.

```text
BinaryLoader, base 0x0, ARM:LE:32:v4t
preScript  SeedCharmeraFunctions.java
postScript ExportCharmeraAnalysis.java
```

seed script는 분석 대상 위치를 disassemble하고 Ghidra 함수 seed를 추가한다.
`created=true`는 Ghidra가 함수 object를 만들었다는 뜻일 뿐 원본 function boundary,
ABI, 실행 여부의 증명이 아니다. exporter는 JSON call graph, incoming xref, direct
call edge, inferred prototype/local 및 각 seed의 decompiler C를 작성한다.

## seed별 결과

|file offset|논리 VA|Ghidra 결과|직접 근거 / 판정|
|---|---:|---|---|
|`0x200`|`0x0`|vector word만 함수화|`18f09fe5`; application 함수가 아님|
|`0x23c`|`0x3c`|reset entry|head `d3f02fe3`; vector xref `0x0→0x3c`|
|`0x2dd48`|`0x2db48`|초기화 aggregator|`0x164→0x2db48` branch, 14 direct calls|
|`0x65b0`|`0x63b0`|event/state dispatcher 후보|caller `0x25668`, event-like branch와 `0x6578` 호출|
|`0x6578`|`0x6378`|dispatcher의 종료/전이 helper 후보|caller `0x63b0`, 두 helper call|
|`0x36274`|`0x36074`|subsystem initialization tail|`0x2db70`에서 call; Ghidra body min이 `0x30ed0`이어서 독립 boundary 불확실|
|`0x2ce24`|`0x2cc24`|초기화 하위 집합|`0x2db6c`에서 call; Ghidra body min `0x2c594`|
|`0x1cbc4`|`0x1c9c4`|camera/video 상태 처리 인접|2 incoming xref, 100개 이상 direct call; hook 불가|
|`0x21c2c`|`0x21a2c`|문자열 draw helper 후보|4 callers, buffer/render/commit처럼 보이는 call chain|
|`0x21370`|`0x21170`|SD updater main|caller `0x257b8`, checksum/64 KiB/256 B loop|
|`0x21818`|`0x21618`|update discovery|caller `0x2e3c`, `C:\\JH_5408*.bin` build와 12-byte compare|
|`0x217b4`|`0x215b4`|updater post-block tail|`0x213a8→0x215b4`, `0x1d20(end+0x10000)` call|
|`0x1d20`|`0x1b20`|wrapped storage/SPI helper|`0x1180 → 0x3060c(arg) → 0x1174`|

## reset 및 bootstrap pseudocode 발췌

Ghidra의 reset decompile은 CPSR/MMIO/RAM 초기화 뒤 logical VA `0x2db48`로 이어지는
전체 경로를 하나의 의사코드로 보여 준다. 이전의 `0x364` branch 관찰과 일치한다.

```c
/* seed 0x23c: shortened */
_DAT_ff000000 = 0;
/* early MMIO / copy / BSS-like loops omitted */
FUN_00031064();
FUN_00036054(0);
FUN_0008cd28();
seed_2ce24();
seed_36274();
/* ... */
FUN_0008d648();
```

`0x2dd48` seed의 observed head는 `1c402de9` (`push` 계열 A32 word)이고,
`0x2db5c→0x31064`, `0x2db6c→0x2cc24`, `0x2db70→0x36074` 등 16개 direct call이
export되었다. 이 위치가 정상 return ABI를 가진 초기화 집합이라는 것은 강해졌지만,
reset이 `BL`이 아닌 branch로 도달하고 이후 task/UI 경계가 미확정이므로 hook point는
아니다.

## 해석 한계

- decompiler type, parameter, local 및 helper 이름은 Ghidra의 정적 추정이다.
- indirect call, IRQ, scheduler/task creation, BootROM, SPI XIP, MMIO 의미는 이 실행으로
  확정되지 않았다.
- 일부 seed는 기존 큰 함수 body 내부로 병합되었다. 예: `0x36274` body minimum은
  `0x30ed0`, `0x2ce24` body minimum은 `0x2c594`이다. 그러므로 seed 위치를 독립적인
  안전 patch boundary로 사용하지 않는다.

상세 direct edge 및 C export는 machine-readable `work/ghidra/exports/function_graph.json`
및 같은 directory의 `pseudocode/`에 보존한다.
