# Phase 3 — Application call graph와 hook 판정

## 관찰된 흐름

```text
vector VA 0x0
  └─ reset VA 0x3c (file 0x23c)
       └─ branch / initialization aggregator VA 0x2db48 (file 0x2dd48)
            ├─ VA 0x2cc24 (file 0x2ce24): low-level init helper set
            ├─ VA 0x36074 (file 0x36274): subsystem init helper set
            └─ other initialization calls

caller VA 0x25668
  └─ VA 0x63b0 (file 0x65b0): event/state dispatcher candidate
       └─ VA 0x6378 (file 0x6578): two helper calls / state transition candidate

multiple application callers
  └─ VA 0x21a2c (file 0x21c2c): string draw helper candidate
```

화살표는 Ghidra export에서 나온 direct branch/call 또는 incoming xref다. runtime
task scheduling 순서, UI state 이름, peripheral 완료 순서는 의미하지 않는다.

## 함수별 ABI 및 호출 맥락

|후보|Ghidra observed body/caller|의사코드로 보이는 역할|ABI 판단|hook 판정|
|---|---|---|---|---|
|`0x2dd48`|VA `0x2db48..0x2dc1f`; incoming `0x164→0x2db48`|여러 init call와 aligned state/global 설정|seed prototype `undefined`, reset branch 진입. live registers/task frame 불명|거부|
|`0x36274`|caller `0x2db48`; body min `0x30ed0`|14 init helper call 후 MMIO-like store|독립 function boundary가 아님|거부|
|`0x2ce24`|caller `0x2db48`; body min `0x2c594`|5 helper call 후 MMIO-like store|독립 boundary/side effect 불명|거부|
|`0x65b0`|caller `0x25668`, body `0x63b0..0x6513`|input/event 결과 code에 따른 분기·service dispatch 후보|entry args, caller loop ownership, return type/global state 불명|거부|
|`0x6578`|caller `0x63b0`, body `0x6378..0x63ab`|`0x8f67c`, `0x25984` call|event context 및 object/global ABI 불명|거부|
|`0x1cbc4`|incoming `0x1c5bc`, `0x1c5cc`|dense camera/video state code|camera pipeline dependency가 너무 큼|거부|
|`0x21c2c`|4 callers: file `0x9a5c`, `0x1badc`, `0x1bb68`, `0x1d580`|string buffer allocate/render/submit 후보|`r0` structure, `r1` data, allocation/ownership/commit ABI 불명|호출 대상 후보만, hook 거부|

`0x65b0`의 Ghidra C는 `0x25a38` 결과와 stack local code를 반복 처리하며
`0x220cc`, `0x21dc8`, `0x21d20`, `0x6578`를 호출한다. 따라서 Phase 2의 단순
"state-like" 판정보다 event/state dispatcher일 가능성은 높아졌다. 다만 caller
`0x25668`의 task 생성·loop 문맥, input completion 여부, display/audio initialization
선행 조건이 아직 복원되지 않았다.

## display 후보의 정확한 정적 증거

`0x21c2c`의 축약 pseudocode는 다음과 같다.

```c
if (*(param_1 + 8) != 0) FUN_00000560();
bytes = (*(ushort *)(param_1 + 4) + 2) * (*(ushort *)(param_1 + 2) + 2);
*(param_1 + 8) = FUN_000637ac(..., bytes * 2, "ap_state_handling_ASCII_str_draw");
if (*(param_1 + 8) == 0) return -1;
if (FUN_000f0e10(*(param_1 + 8)) == 0) {
    FUN_000f0138(...);
    FUN_000f04f4(..., *(param_1 + 8));
}
FUN_00024c9c(*(param_1 + 8), param_2, 2);
FUN_0008f67c(*DAT_00021a18, param_1 | 0xc0000000);
return 0;
```

이것은 buffer allocation/formatting/commit처럼 보이는 strong static pattern이다. 그러나
`param_1` structure layout, pixel format, queue ownership, `0x8f67c`가 display submission인지,
그리고 호출 가능한 global context는 증명되지 않았다. 따라서 `screen` HAL이나 stock
function 호출 코드를 만들지 않는다.

## hook 승인 결과

**사용 가능한 실제 synth hook은 찾지 못했다. 실험 patch를 만들지 않았다.**

가장 작은 다음 정적 blocker는 `0x25668 → 0x63b0` caller 경로를 function boundary부터
task creation/loop까지 역추적해 다음 네 가지를 증명하는 것이다.

1. `0x63b0` 이전에 LCD, input, audio 관련 초기화가 완료되는가.
2. camera UI 전환 전의 별도 task/state boundary인가.
3. patch site의 original instruction, live `r0-r12/lr`, stack ownership과 복귀 경로가
   재현 가능하게 고정되는가.
4. update-mode discovery/updater 경로가 그 hook에 의존하지 않는가.

이 네 조건, tail layout 검증, 별도 복구 가능한 하드웨어의 runtime 검증 전에는 hook
수용 또는 stock app 대체를 주장하지 않는다.
