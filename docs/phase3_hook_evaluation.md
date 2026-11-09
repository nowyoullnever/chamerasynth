# Phase 3 — Hook 후보 평가

## 결론

**승인 가능한 hook: 없음. experimental patch: 없음.**

Ghidra 실행은 이전 후보들의 caller/callee 및 일부 ABI 추정을 크게 개선했지만,
application 교체에 필요한 post-hardware/pre-camera-UI boundary와 안전한 return contract를
증명하지 못했다.

|후보 file offset|관찰된 bytes / xref|통과한 부분|미통과 안전 요건|판정|
|---:|---|---|---|---|
|`0x2dd48`|head `1c402de9`; reset 경로에서 incoming `0x364→0x2dd48`|초기화 call graph 회수|branch 진입, caller frame 없음, hardware/UI 완료 여부 없음|거부|
|`0x36274`|`0x2db70` direct call, 14 helper call|init 하위 집합 확인|Ghidra body가 `0x30ed0`부터여서 standalone boundary 아님|거부|
|`0x2ce24`|`0x2db6c` direct call, 5 helper call|init 하위 집합 확인|body min `0x2c594`; peripheral side effect/return contract 불명|거부|
|`0x65b0`|caller `0x25668`; 12 direct helper call|event/state dispatch 후보 강화|task ownership, args/globals, camera/UI 전 경계, safe return 불명|거부|
|`0x1cbc4`|camera-adjacent dense graph|실제 code body/graph 회수|camera pipeline·resource lifecycle와 강하게 결합|거부|
|`0x21c2c`|4 callers, draw helper chain|display service 후보|renderer helper일 뿐 application transition 아님|거부|

## patch site 및 relocation 결정

`0x2dd48`에서 erased tail candidate `0x1aee00`로의 A32 direct branch는 *가정 mapping*
기준 ±32 MiB encoding 범위에는 든다. 하지만 branch encoding 가능성은 hook validity나
tail 실행 가능성을 보장하지 않는다.

- tail `0x1aee00..0x1fffff`는 FF 바이트 관찰만 있다.
- header word `0x10 = 0x001b0000`의 의미가 미확정이다.
- tail virtual address로 보이는 aligned 값 176개 및 resource-like data cluster가 있어
  computed reference, image-size contract, resource bound를 배제하지 못했다.
- actual flash execute mapping, cache, RAM/stack budget, updater write range가 미확정이다.

따라서 insertion region은 여전히 `trust = "unverified"`이고, manifest의
`status = "analysis-only"`를 유지한다. 어느 위치에도 branch replacement나 synthesized
payload bytes를 쓰지 않았다.

## 분석용 patch framework의 상태

`tools/firmware_inject.py`는 source identity, alignment, protected range, expected
original bytes와 A32 branch range를 확인한다. image output에는 명시적으로
`experimental-qualified`, reviewed insertion region, enabled patch 및
`--allow-experimental`이 모두 있어야 한다. 현재 committed manifest는 이 조건을 충족하지
않으므로 output을 생성할 수 없다.

updater candidate `0x20000..0x21fff`와 SPII/startup `0x0..0x2dfff`는 manifest의
protected range에 포함되어 있다. tests는 updater site `0x21370` patch 시도도 거부되는지
확인한다.
