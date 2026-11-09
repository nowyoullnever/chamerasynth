# Phase 2: Hook 후보 평가

## 결론

**승인 가능한 hook 후보는 없다.** 아래 위치들은 분석 seed일 뿐 patch target이 아니다. injection manifest에는 enabled patch가 없고 `status = "analysis-only"`다.

|후보|원본 bytes/동작|ABI·return|필수 선행 초기화|위험|판정|
|---|---|---|---|---|---|
|`0x2dd48`|`E92D401C`; 여러 init call|함수 자체는 `E8BD801C` return, 하지만 reset 경로는 `0x364`의 `B`로 진입|불명: 이 함수가 실제로 어떤 driver/UI를 준비하는지 미완료|return frame 없음; early boot 또는 later app인지 미확정|거부|
|`0x65b0` 부근|state-like loop/calls/조건 분기|entry/args/return 미확정|`0x6578` startup-adjacent routine 및 여러 state service 가능성|scheduler인지 UI인지 불명, state/global 훼손 위험|거부|
|`0x1cbc4` 부근|camera video state code와 인접|정확한 function boundary/ABI 미확정|camera pipeline 가능성|camera subsystem에 너무 가까우며 UI 진입 증거 없음|거부|
|`0x21c2c`|string draw 관련 code, prologue `push {r4,r5,r6,lr}`|r0/r1 및 stack locals 관찰; semantics 미확정|display/resource services|렌더 helper이지 application transition 증거 없음|거부|

## hook 승인 요건

후보를 `experimental-qualified`로 올리려면 다음을 모두 충족해야 한다.

1. Ghidra caller/callee graph로 task/state entry임을 확인한다.
2. patch site의 original bytes, function boundary, caller convention, live registers, stack ownership을 확인한다.
3. 해당 시점 이전에 LCD/input/audio/power/SD init이 끝났음을 control flow로 확인한다.
4. update mode detection과 recovery UI가 해당 hook에 의존하지 않음을 updater path 기준으로 확인한다.
5. original path로 복귀하거나 controlled reset하는 정확한 behavior를 설계·정적 검증한다.
6. separate recoverable test hardware에서만 runtime 검증한다.

Phase 2에서는 위 조건을 만족한 patch를 만들지 않는다.

