# Phase 3 — SD updater decompilation

## 관찰된 제어 흐름

```text
caller VA 0x257b8
  └─ updater main VA 0x21170 (file 0x21370)
       ├─ path/file handles, read helpers, UI/status helpers
       ├─ byte accumulation / expected value compare
       ├─ 0x10000-aligned outer block operation
       ├─ 0x100-byte inner operation and readback-like compare
       └─ branch/call to VA 0x215b4 (file 0x217b4)
            └─ wrapper VA 0x1b20 (file 0x1d20)
                 ├─ VA 0x1180
                 ├─ VA 0x3060c(argument)
                 └─ VA 0x1174

caller VA 0x2e3c
  └─ discovery VA 0x21618 (file 0x21818)
       └─ build `C:\\JH_5408*.bin`; compare 12 bytes with `202505201029`
```

## `0x21818`: filename discovery와 timestamp gate

Ghidra pseudocode shows `FUN_000906b8()` result check, then strings `C:\\JH_`,
`5408`, `*.bin`을 하나의 buffer에 붙이고 `FUN_000e2cf0`를 호출한다. 성공 시
`FUN_000e2c54()` 뒤 structure-like pointer `+0x19`와 ASCII `202505201029` 사이 12 byte
비교 결과에 따라 `1`을 반환한다.

이는 `JH_5408<12 decimal timestamp>_<8 hex>.bin` filename family와 stock build timestamp
gate가 존재한다는 강한 정적 근거다. `FUN_000e2cf0`가 FAT root scan인지, `+0x19`가 filename
field인지, compare 결과의 sign convention은 helper/type 복원 전에는 명칭으로 확정하지 않는다.

## `0x21370`: updater main

Ghidra export상 body는 VA `0x21170..0x215b3`, caller는 VA `0x257b8`이다. 직접 call에는
read/open-like cluster, UI/status-like cluster, `0x1aec`, `0x119c`, `0x4cc`, `0x1b20`가
포함된다. decompiler가 회수한 핵심 구조는 다음과 같다.

```c
/* shortened; helper names are addresses, not semantic labels */
/* reads data, accumulates a byte value, compares it with expected value */
for (outer = ...; outer < ...; outer += 0x10000) {
    if (seed_1d20(outer) == 0) {
        for (inner = 0; inner < 0x10000; inner += 0x100) {
            FUN_0000119c(...);
            /* transfer/readback-like work of 0x100 bytes */
            FUN_00001aec(...);
            FUN_000004cc(...);
        }
    }
}
/* control reaches VA 0x215b4 */
```

따라서 checksum-like byte accumulation/compare, 64 KiB outer granularity, 256-byte inner
granularity, write/readback-like two-phase operation은 강한 정적 관찰이다. `0x1aec`,
`0x119c`, `0x4cc`의 precise erase/program/read semantics, start/end address units, chip
address wrapping과 return values는 아직 확정하지 않는다.

## `0x217b4`와 `0x1d20`

KCP가 erase point라고 주장한 file `0x217b4`는 standalone updater entry가 아니라 main
body 뒤의 post-block code로도 해석될 수 있다. Ghidra incoming xref는 `0x213a8→0x215b4`와
`0x215a8→0x215b4`이고 첫 direct call은 VA `0x215b8→0x1b20`이다. decompile은
`r10 + 0x10000` 형태의 end-address-like argument를 wrapper로 전달한다.

```c
undefined4 seed_1d20(undefined4 arg) {
    FUN_00001180();
    value = FUN_0003060c(arg);
    FUN_00001174();
    return value;
}
```

즉 `0x217b4`가 `0x1d20(end + 0x10000)` wrapper를 호출한다는 사실은 확인했다. 그러나
central helper `0x3080c`의 command, `0x1180/0x1174`의 lock/critical-section semantics,
SPI opcode, range/wrap은 미분석이다. 따라서 이를 erase proof나 30-block workaround의
safety proof로 승격하지 않는다.

## updater 판정

|질문|Phase 3 판정|
|---|---|
|filename discovery|강한 정적 근거|
|12-byte timestamp compare|강한 정적 근거|
|byte-sum checksum|accumulation/compare 구조 확인; exact filename field/algorithm contract는 helper 추적 필요|
|flash erase/program/readback|granularity와 two-phase-like loop 확인; exact helper semantics 미확정|
|`0x217b4` erase|미확정. post-block wrapper call만 확인|
|updater RAM/SPI execute 또는 self-overwrite|미확정|
|2 MiB wrap / 30-block deployment|미확정, 사용 금지|

다음 최소 분석은 VA `0x3060c`(file `0x3080c`), `0x1180`(file `0x1380`),
`0x1174`(file `0x1374`)의 callers/dataflow와 SPI MMIO access를 복원하는 것이다.
