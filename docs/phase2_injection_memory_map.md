# Phase 2: Injection 메모리와 branch 분석

## tail 후보

|항목|값|상태|
|---|---|---|
|파일 범위|`0x1aee00..0x1fffff`|모두 `0xff`로 관찰|
|크기|`0x51200` (332,288 bytes)|산술적으로 확인|
|payload mapping 가정시 VA|`0x1aec00..0x1ffdff`|가설; file `0x200`을 logical zero로 둔 경우|
|header word|`0x10`의 LE `0x001b0000`|의미 미확정|

이 영역은 executable/writable/free space로 승인되지 않았다. whole-image aligned-value scan에서 가정 VA tail 범위에 들어가는 값이 176개 있었고, resource-table처럼 보이는 cluster가 `0x14c428`부터 있다. branch scan의 tail target 72개도 code/data 분리가 되지 않아 xref 증거가 아니다. computed pointer, resource/header bounds, update image size contract도 배제하지 못한다.

## branch reachability

가정 mapping에서 `0x2dd48` site는 VA `0x2db48`, tail start는 VA `0x1aec00`이다. direct A32 `B/BL` delta는 `0x1810b0`으로 ±32 MiB 범위 안이다. 따라서 **branch encoding 자체는 가능**하다. 이는 hook의 안전성, tail의 사용 가능성, runtime flash execute 가능성을 의미하지 않는다.

## injection framework guard

`patches/manifest.example.toml`은 tail을 `trust = "unverified"`로 표시한다. `tools/firmware_inject.py`는 다음을 hard-fail한다.

- source size/SHA-256 mismatch
- non-FF declared insertion region, range/overlap/alignment 오류
- protected range 수정, expected original bytes mismatch
- A32 branch alignment/range 오류
- unresolved/analysis-only manifest image output
- runtime mapping confidence가 `verified`가 아닌 A32 branch patch
- immutable source image와 같은 output path

실험 image output에는 `status = "experimental-qualified"`, `--allow-experimental`, reviewed region, exact patch original bytes가 모두 필요하다. 현재 manifest는 조건을 만족하지 않으며 output image가 생성되지 않는다.

