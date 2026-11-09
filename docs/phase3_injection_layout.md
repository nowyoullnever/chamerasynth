# Phase 3 — Injection layout 판정

## 현재 layout

|범위|상태|증거/제약|
|---|---|---|
|`0x000000..0x0001ff`|보호|SPII/SRIy container/header, semantics 미확정|
|`0x000200..0x0002dfff`|보호|vectors, reset/startup, bootstrap과 초기화 aggregator|
|`0x020000..0x021fff`|보호|Ghidra로 확인한 updater discovery/main/post-block path 포함|
|`0x1aee00..0x1fffff`|unverified tail candidate|전부 FF이나 executable/free/writable/runtime mapping 증거 없음|

payload-base hypothesis에서 tail의 logical VA는 `0x1aec00..0x1ffdff`다. 이 계산은
file `0x200`을 logical zero로 놓은 결과이며 runtime address나 flash execution proof가 아니다.

## Ghidra가 바꾼 점과 바꾸지 못한 점

Ghidra는 startup/update 범위를 function/control-flow evidence로 더 명확히 했다. 따라서
protected updater window를 유지하는 근거가 강해졌다. 반면 tail을 향한 모든 data xref,
resource index/length, header image-size field, computed pointer, BootROM/fetch mapping을
분류하지 않았으므로 tail verdict는 변하지 않았다.

- Phase 2 scan: tail VA 범위처럼 보이는 aligned value 176개, branch target 72개를 발견.
- Phase 3: 이 값들이 code pointer인지 resource/data field인지 Ghidra dataflow로 분류하지
  못했다.
- header file `0x10`의 `0x001b0000`은 tail start와 근접하지만 field meaning을 알 수 없다.

## patch/insertion 결과

실험 insertion payload, branch patch, altered firmware, SD package를 만들지 않았다.
`patches/manifest.example.toml`은 계속 `analysis-only`이며 tail은
`trust = "unverified"`이다. `tools/firmware_inject.py`는 `analysis-only` manifest 또는
unreviewed region에서 image output을 hard-fail한다.

tail을 `reviewed`로 바꾸기 위한 최소 증거는 다음과 같다.

1. header/resource/index field가 tail을 포함하지 않는다는 xref/dataflow 증명.
2. code/data branch target 72개와 aligned-value 176개의 의미 분류.
3. image-size/update write range와 tail의 충돌 부재.
4. physical execution mapping, RAM/stack/cache contract 및 recovery path의 별도 증거.

이 조건을 충족하기 전에는 branch reachability나 FF fill을 insertion 권한으로 해석하지 않는다.
