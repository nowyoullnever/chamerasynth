# Phase 5 최종 보고서

## 결론

1. `0x5025 → 외부 0x108 → 0x21170`은 정적으로 추적됐다. 그러나 `0x5025`를 내부 큐에 생산하는 함수와 조건은 확인되지 않아 전체 이벤트 생성 경로는 **미완료**다.
2. 카메라 전용 로직과 필수 시스템 서비스의 완전 분리는 되지 않았다. 큐/스케줄러, 시작 초기화, 간접 백엔드, 종료 경로는 보존 대상으로 분류했으며 `0x6134`는 UI·오디오·서비스가 혼합되어 있다.
3. 근거가 가장 강한 전략은 현재 **패치하지 않는 것**이다. 기존 `0x2572c` 후보와 `0x63b0` 대체는 업데이트 릴레이를 제거할 수 있다. UI 전용 콜백/상태가 확인된 뒤에만 재평가한다.
4. 실제 펌웨어 패치, 수정 이미지, SD 업데이트 패키지, 장치 작업은 생성·수행하지 않았다. 매니페스트는 `analysis-only` 상태다.
5. WAV 리소스에서 소프트웨어 재생 요청 체인(`0x1e844 → 0x25984 → 0x13110 → 0x12f0c`)은 확인했다. DAC/PWM/DMA/PCM 출력 함수는 아직 확인하지 못했다.
6. 첫 실제 신스 펌웨어 시험 전 남은 정확한 작업은 다음 두 게이트다: (a) 내부 `0x5025` 생산자와 UI 전용 상태/콜백의 ABI·반환·큐 소유권을 추적하고 업데이트 릴레이/정리 경로가 보존됨을 입증할 것, (b) 실행 가능한 삽입 영역과 업데이터의 이미지 길이·지우기·쓰기·재부팅 동작을 독립 검증할 것. 오디오에는 `0x12f0c`의 간접 대상 및 버퍼-장치 경로 추적이 추가로 필요하다.

## 재현 산출물

- 이벤트: `ghidra_scripts/ExportPhase5EventLifecycle.java`, `work/phase5-event/phase5_event_graph.json`, `work/phase5-event/pseudocode/`
- 오디오: `ghidra_scripts/ExportPhase5Audio.java`, `work/phase5-audio/audio_handle_graph.json`, `work/phase5-audio/pseudocode/`
- 레이아웃: `tools/audit_tail_layout.py`, `work/phase5-tail-audit.json`
- 논리 모델: `tools/event_lifecycle_model.py`, `tests/test_event_lifecycle_model.py`

테스트와 모델은 호스트 측 정적/논리 검증일 뿐이며, 하드웨어 안전성·부팅·업데이트·오디오 출력을 증명하지 않는다.
