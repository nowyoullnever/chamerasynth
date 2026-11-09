# Phase 2: 애플리케이션 진입 분석

## 분석 상태

Ghidra의 raw-binary manual import는 이 환경에 Ghidra가 설치되어 있지 않아 수행할 수 없었다. 대신 payload base 가설(`file offset 0x200` ↔ logical address `0`)을 **주소 계산용으로만** 사용해 A32 branch/call을 정적으로 추적했다. 아래의 `VA`는 이 가설의 산물이며 물리 runtime address로 확정되지 않았다.

## 확인된 startup graph

```text
reset 0x00023c
  └─ early MMIO / RAM / mode-stack initialization
     └─ 0x000364: B 0x0002dd48
        └─ 0x0002dd48: initialization aggregator
           ├─ BL 0x31264, 0x36254, 0x8cf28, 0x2ce24, 0x36274
           ├─ BL 0x2e96c (r0=8 / 9)
           ├─ BL 0x2eba4 (8,0x2a) / (9,6)
           ├─ BL 0x325f0 (r0=0x28), 0x668d8 (5,6,4)
           └─ BL 0x7d8, 0x31b4c, 0x9012c, 0x31264, 0x8d848
```

|함수 후보 (file offset)|직접 근거|판정|
|---|---|---|
|`0x0002dd48..0x0002de1c`|시작 `E92D401C` (`push {r2,r3,r4,lr}`), 끝 `E8BD801C` (`pop {r2,r3,r4,pc}`), 위 call sequence|초기화 aggregator. normal return ABI를 가지지만 reset은 `BL`이 아닌 `B`로 진입하므로 application entry/hook으로 확정 불가|
|`0x00036274`|`0x312fc`, `0x326f8`, `0x3661c`, `0x345d4`, `0x33a68`, `0x33c40`, `0x2e404`, `0x31704`, `0x31c98`, `0x32bf8`, `0x2efec`, `0x31294`, `0x30ff4`, `0x30fd4` 호출 뒤 `0x310d0`으로 branch|다수 subsystem 초기화 aggregator 후보. subsystem 이름/순서 미확정|
|`0x0002ce24`|`0x2cd88`, `0x2c918`, `0x2ca0c`, `0x2ca84`, `0x2c7d0` 호출 뒤 `0x2c794` branch|초기화 하위 aggregator 후보|
|`0x000065b0` 부근|`0x6104`, `0x1e434`, `0x6334`, `0x2d51c`, `0x25c38` 호출 및 stack event/result 분기|state/event loop 후보. scheduler 또는 UI dispatcher로는 미확정|

## 원본 camera application entry

현재 증거로는 “essential hardware initialization 뒤, camera UI 직전”의 정확한 application entry를 분리하지 못했다. 따라서 다음 사항도 미확정이다.

- RTOS/task scheduler의 entry 및 task-create ABI
- UI state-machine의 최초 state
- main menu/camera launch transition
- button event dispatcher와 camera app의 연결

`0x2dd48`에 branch가 도달한다는 사실은 확인했지만, 이 위치에서 return하거나 원래 caller 상태를 보존할 수 있다는 증거가 없다. 이를 hook으로 사용하지 않는다.

## Ghidra 후속 절차

1. raw payload `0x200..0x1fffff`를 ARM little-endian A32로 import한다. 초기 image base는 `0`과 별도 candidate base를 **분리 프로젝트**로 둔다.
2. `0x3c` vector target, reset `0x23c`, `0x2dd48`의 function boundaries를 byte/branch target과 비교한다.
3. `0x65b0`, `0x1c0a8`, `0x1cbc4`, `0x21c2c`를 xref/caller graph로 추적하여 task/state transitions를 분류한다.
4. 발견한 function address는 file offset, assumed VA, 근거, confidence를 함께 기록한다.

