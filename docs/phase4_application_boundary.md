# Phase 4 — 애플리케이션 교체 경계

## 결론

정적으로 근거가 있는 **조건부 교체 경계**를 찾았다. shared event loop의 event `0x100`
분기에서 camera-state handler만 호출하는 site가 대상이다.

|항목|값|신뢰도|
|---|---|---|
|공유 loop entry|VA `0x25668`, file `0x25868`, body `0x25668..0x257ef`|중간|
|camera handler call site|VA `0x2572c`, file `0x2592c`, bytes `1f83ffeb` (`BL 0x63b0`)|높음 (정적)|
|camera handler|VA `0x63b0`, file `0x65b0`|높음 (정적)|
|updater event dispatch|VA `0x257b8`, file `0x259b8`, bytes `6ceeffebb6ffffea` (`BL 0x21170; B 0x2569c`)|높음 (정적)|

이것은 firmware patch 승인이나 device 실행 증명이 아니다. Tail/insertion region과
custom handler의 required state가 미확정이므로 original bytes를 변경하지 않았고, manifest는
해당 범위를 protected로 유지한다.

## 공유 event loop

`0x25668`은 `0x24d7c` setup 후보와 `0x8f67c` 이후 반복적으로 `0x8f560`에서 outer event를
받는다. event word의 low 9 bit가 switch ID다.

```text
boot-path reference VA 0x2db34 → VA 0x25668       (task-create/registration type 미확정)
VA 0x25668: receive outer event
  0x100 → VA 0x2572c: BL VA 0x63b0                (camera state handler)
  0x105 → context callback pointer
  0x108 → VA 0x257b8: BL VA 0x21170; B loop       (updater main)
  other IDs → existing common handlers / loop
```

`0x25668` entry head는 `fe4f2de9c2fdffeb50561fe5401fa0e3`이다. Ghidra C는 caller-owned
`local_2c` address를 `0x63b0`에 전달한다. `0x63b0`은 반복적으로 inner queue를 처리한 뒤
return하고, caller는 loop로 계속 진행한다. 따라서 `0x25668` 전체는 ordinary helper보다
장기 task/event-loop에 가깝지만, `0x2db34` reference가 task creation인지 callback
registration인지는 아직 확정하지 못했다.

## event message와 ABI

`0x25a38` (VA, file `0x25c38`, head `fc412de9…`)은 queue receive/copy 형태다.
성공 시 slot word 0을 output event word에 복사하고, 뒤 byte payload를 destination에 최대
요청 길이만큼 복사한 뒤 slot word를 0으로 만든다. `0x63b0`은 `0x25a38(..., &event_code,
..., 0x28)`을 사용한다.

```text
inner message slot
  +0x00  uint32 numeric event/state code
  +0x04  payload bytes (consumer requested maximum: 0x28)
```

`0x25984` (file `0x25b84`, head `f84f2de9…`)은 반대로 code/payload를 slot에 넣고
`0x8f67c` 또는 `0x8f73c`로 signal한다. 따라서 Ghidra가 `0x63b0`의 `local_24`를 pointer/code로
표현한 것은 type recovery 오류다. 관찰된 numeric code는 `0x7000..0x7042`, `0x5013`,
`0x5025`다.

교체 handler의 **최소 정적 ABI**는 `r0 = event-loop stack의 transient message local`이다.
그 pointer를 retain/free하거나 task return 경로를 바꾸면 안 된다. A32 prologue/epilogue는
callee-saved register와 `sp/lr` 보존이 필요한 일반 ABI와 일치하지만, compiler ABI와 return
value 의미는 runtime으로 검증되지 않았다.

## Strategy 평가

|순위|전략|정확한 위치|판정|
|---:|---|---|---|
|1|C. camera state handler 대체|VA `0x2572c`, file `0x2592c`, `BL 0x63b0`|조건부 최상. outer queue, event `0x108` updater dispatch, other system handler를 남긴다. custom handler가 정상 return해야 한다.|
|2|B. init 후 redirect|`0x24d7c` 뒤 loop 진입 인접|거부. separate post-hardware/pre-camera-menu branch를 아직 분리하지 못했다. loop를 우회하면 updater event와 common callback을 잃을 수 있다.|
|3|A. UI task entry 대체|VA `0x25668`, file `0x25868`|거부. shared loop 자체이며 `0x105`, `0x108`과 여러 message handler를 포함한다.|

`0x63b0`만 camera-exclusive인지도 완전히 증명된 것은 아니다. 다만 common helper
`0x21dc8`, `0x21d20`, `0x220cc`은 다수 caller가 있으므로 camera 전용 API로 삭제하면 안 된다.

## update lifecycle 판정

update discovery는 VA `0x21618`, file `0x21818`이고 VA `0x3070`에서 call된다. 포함 함수는
VA `0x2e3c`, file `0x303c`, caller reference `0x5df8→0x2e3c`다. 이 함수는 storage-like
초기화 후 discovery를 호출하고 failure면 `C:\\DCIM`/`C:\\SPIDCIM` path로 진행한다.

따라서 discovery가 camera handler `0x63b0` 안에 있다는 증거는 없다. updater main은 shared
loop의 `0x108` event에서 실행되고 끝나면 loop로 branch한다. 단, `0x2e3c`와 `0x25668`의
ultimate boot ordering은 미복원이다. **handler-only 대체라면 stock updater execution path는
정적으로 남지만, SD recovery가 보장된다고 말할 수는 없다.**

## 다음 blocker

1. `0x25984` caller graph에서 outer event `0x100` producer와 physical button relation을 찾는다.
2. `0x63b0` 앞의 common context/queue/global initialization 목록을 확정한다.
3. `0x2db34` reference type과 `0x5df8→0x2e3c` boot ordering을 복원한다.
4. tail reference/layout 및 executable mapping을 해소한다.
