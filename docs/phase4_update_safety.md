# Phase 4 — Updater 안전성 및 SPI 경계

## 확인된 정적 SPI operation

`0x215b4`는 독립 updater entry가 아니라 VA `0x21170` main body 뒤의 post-update tail이다.
main은 shared event loop의 event `0x108`에서 VA `0x257b8`을 통해 호출되고, 이후 loop로
branch한다.

|작업|call chain|정확한 code evidence|정적 판정|
|---|---|---|---|
|64 KiB erase|`0x21170 → 0x1b20 → 0x3060c`|`0x30664: mov r0,#1`; `0x3066c: mov r0,#0xd8`; `0x30674..7c: arg & 0xffff0000`|SPI NOR 64 KiB erase, 높음|
|WREN|program path `→0x3028c`|`0x302b8: mov r0,#6`|opcode `0x06`, 높음|
|256 B program|`0x21170 → 0x1aec → 0x30800`|opcode `0x02`, `arg & 0xffffff00`, length `0x100`|높음|
|256 B verify read|`0x21170 → 0x119c → 0x306b4`|opcode `0x03`, `arg & 0xffffff00`, length `0x100`|높음|
|status wait|`0x30400 → 0x303a4`|opcode `0x05`, bit 0 set 동안 loop|높음|

machine-readable table: `docs/phase4_update_operations.json`. Full focused export:
`work/ghidra/phase4_updater/updater_deep.json`.

## main loop와 r10

VA `0x21170` prologue는 `r4..r11,lr`를 save한다. checksum/read loop에서 `r10`은 progress
offset으로 사용된다: `0x21238`에는 zero-setting path가 있고, `0x2129c`에서 returned byte count를
더며, `0x2124c`/`0x212ac`에서 file length `r5`와 비교한다. outer transfer granularity는
`0x10000`, inner transfer granularity는 `0x100`이다.

post tail의 original bytes at file `0x217b4` are `40 0b 8a e2 58 81 ff eb`:

```text
VA 0x215b4  ADD r0,r10,#0x10000
VA 0x215b8  BL  0x1b20
```

`0x1b20`는 `0x1180`, `0x3060c(arg)`, `0x1174` 순서의 wrapper다. 즉 post operation은
`r10 + 0x10000` block address의 `0xD8` erase를 요청한다.

## 2 MiB/30-block 판정

code-level arithmetic은 다음을 보인다.

```text
input progress 0x200000 → post argument 0x210000
input progress 0x1e0000 → post argument 0x1f0000
```

그러나 firmware는 erase request address에 `0x1fffff` mask를 적용하지 않고 high address
word를 controller request에 전달한다. physical flash capacity, address pins, controller address
decode가 이 image만으로 확정되지 않았다. 따라서 `0x210000`이 physical `0x010000`으로 wrap해
block 1을 erase한다는 주장은 **미증명**이며, 30-block 방식도 안전성 증명이 아니다.

Keychain Camera Plus `pack_sd_firmware.py`는 2 MiB input이면 tail이 all-FF가 아닌 경우에도
경고만 출력하고 두 branch 모두 `raw_data[:0x1e0000]`로 자른다. non-empty tail을 silent
preservation 없이 제외하는 결함이다. 이 프로젝트는 해당 packer를 실행하거나 SD package를
생성하지 않는다.

## injection/tail과 updater

tail `0x1aee00..0x1fffff`은 FF fill만으로 보존 영역이라 할 수 없다. updater의 actual
file-length contract와 physical address decoding을 아직 정하지 못했고, tail에 대한 direct
Ghidra references도 존재한다. 따라서 updater가 tail을 보존/erase하지 않는다는 결론은 낼 수
없다.
