# Kodak Charmera Synth — Phase 4 최종 보고서

## 최종 판정

1. **애플리케이션 교체 경계:** 정적으로 근거가 있는 조건부 후보를 찾았다. VA `0x2572c`
   (file `0x2592c`)의 original `BL 0x63b0`은 shared event loop의 event `0x100`에서만 camera
   state handler를 호출한다. 이것이 현재 가장 안전한 replacement mechanism 후보다.
2. **updater 도달성:** handler-only 대체는 event `0x108 → 0x257b8 → 0x21170` branch를 그대로
   남긴다. update discovery는 별도 VA `0x2e3c → 0x21618` path에서 확인됐다. 그러나 complete
   boot ordering과 SD recovery는 미증명이다.
3. **driver interface:** display work-item/queue와 generic event message ABI는 일부 회수했다.
   physical button mapping과 PCM-to-hardware playback chain은 발견하지 못했다.
4. **offline prototype:** `firmware/synth_event_handler_prototype.S`를 추가했다. `r0` event
   pointer를 dereference/retain하지 않고 즉시 return하는 별도 ARM ELF build 대상이다. firmware에
   link, inject, package하지 않았다.
5. **patch/image:** 생성하지 않았다. tail과 executable mapping이 unverified이므로 manifest는
   analysis-only이고 hook site도 protected다.

## 구현된 정적 경계

```text
shared event loop VA 0x25668 (file 0x25868)
  event 0x100 → VA 0x2572c: BL VA 0x63b0  ← custom handler 후보
  event 0x108 → VA 0x257b8: BL VA 0x21170 → B shared loop
```

custom handler는 caller-owned stack message pointer `r0`를 단기 입력으로만 사용하고 정상
return해야 한다. 그 외 shared loop, `0x105` callback, updater dispatch를 대체해서는 안 된다.

## 검증된 범위

- Ghidra focused app graph: `work/ghidra/exports/phase4-app/phase4_application_graph.json`
- Ghidra focused updater graph: `work/ghidra/phase4_updater/updater_deep.json`
- Ghidra focused driver/tail graph: `work/phase4-driver-tail/driver_tail_graph.json`
- updater operation table: `docs/phase4_update_operations.json`
- original source SHA-256 lock 및 offline tests 유지

## first executable synthesizer test의 정확한 다음 행동

`0x25984`의 callers를 따라 outer `0x100` event producer와 `0x63b0` 전 context initialization을
완성하고, tail references/header/update length/execution mapping을 별도 검증한다. 그 다음에만
별도 recovery 가능한 hardware에서, **handler call contract를 유지하는 최소 no-MMIO routine**의
runtime test를 검토할 수 있다. 현재 장치는 recovery connection이 없으므로 physical test는
권한 밖이다.

이 단계 전에는 DSP/UI 구현, firmware branch replacement, SD updater package를 시작하지 않는다.
