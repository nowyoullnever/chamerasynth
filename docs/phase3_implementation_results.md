# Phase 3 — 구현 결과와 종료 판정

## 결과 요약

|요청 항목|결과|
|---|---|
|실제 Ghidra 실행|완료: Ghidra 12.2 headless, JDK 25, `ARM:LE:32:v4t` payload import|
|Ghidra project / graph / pseudocode 보존|완료: ignored `work/ghidra/projects/CharmeraA32`, `work/ghidra/exports/`|
|startup/application/updater function recovery|완료: 지정 seed 13개를 graph/JSON/C export|
|application hook|미발견 / 거부|
|insertion layout 확정|미확정: FF tail은 unverified 유지|
|synth hardware driver ABI|미확정: display 후보만 call graph 회수|
|updater model|discovery, timestamp compare, checksum-like loop, block granularity를 정적으로 확인; SPI helper semantics는 미확정|
|firmware patch / update package|생성하지 않음|
|physical camera/USB/SD/SPI 작업|수행하지 않음|

## 새 구현물

- `tools/prepare_ghidra_payload.py`: SHA-256-locked source에서 analysis payload만 생성.
- `tools/run_ghidra_analysis.ps1`: pinned local Ghidra/JDK로 reproducible headless import.
- `ghidra_scripts/SeedCharmeraFunctions.java`: named seed 및 A32 decode.
- `ghidra_scripts/ExportCharmeraAnalysis.java`: graph JSON과 per-function pseudocode export.
- `tests/test_ghidra_pipeline.py`: source immutability, mapping, script import contract, generated graph edge/boundary를 검사.
- `tests/test_firmware_inject.py`: committed updater protected window에 patch를 시도하면 거부되는지 검사.

## 검증 범위

unit tests는 source identity, output boundary guard, A32 branch codec, graph mapping/selected
edges, Ghidra script contract만 검증한다. 성공한 tests나 decompiler output은 hardware
execution, correct peripheral API, update compatibility, safe flashing을 의미하지 않는다.

## 정확한 최소 blocker

현재 가장 작은 blocker는 `0x25668 → 0x65b0` 경로의 scheduler/task context와
post-hardware/pre-camera-UI boundary를 증명하지 못한 것이다. 이에 독립적으로 tail의
reference/layout/execution mapping과 updater SPI helper `0x3080c` semantics도 미확정이다.
그러므로 다음 단계는 patch 작성이 아니라 이 세 dataflow graph의 정적 복원이다.
