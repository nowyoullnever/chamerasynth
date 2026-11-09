# Phase 2: 재사용 driver 후보

파일 offset은 함수 주소가 아니다. 문자열 인접 instruction은 분석의 출발점일 뿐 API declaration이 아니다.

|영역|후보 entry/범위|관찰 근거|인자/반환·의존성|신뢰도|판정|
|---|---|---|---|---|---|
|startup state|`0x6578..0x65a8`|`state_startup_init` string `0x6558` 인접; `0x8f87c`, `0x25b84` 호출, `E8BD8008` return|entry association 및 argument/return semantics 미확정|낮음|재사용 불가, xref 필요|
|event/state candidate|`0x65b0` 이후|subcalls 및 stack result branch|scheduler/event dispatcher인지, global state인지 미확정|낮음|재사용 불가|
|display init candidate|`0x1670c..0x16720`|`ap_display_init` string `0x166fc` 인접; r0를 통해 literal-derived 값 store 후 return|r0가 context pointer일 가능성; literals/side effects 미확정|낮음-중간|직접 호출 금지|
|string drawing candidate|`0x21c2c..0x21d14`|`ap_state_handling_str_draw` string `0x21bf4`; prologue, r0/r1, calls `0x639ac`,`0xf1010`,`0xf0338`,`0xf06f4`,`0x24e9c`,`0x8f87c`|string format/context, rendering surface, return semantics 미확정|낮음-중간|display call graph 추적|
|resource init candidate|`0x24034` 부근|`ap_state_resource_init` string `0x2400c` 인접; r0–r3/stack 사용|function boundary/association 미확정|낮음|재사용 불가|
|audio|미식별|`CLICK.WAV` 등 asset 및 DMA-related strings|DAC FIFO, PCM format, DMA/IRQ entry, init globals 전부 미확정|없음|재사용 불가|
|button/GPIO|미식별|state loop 후보만 존재|event encoding, GPIO/IRQ, debounce, queue 미확정|없음|재사용 불가|
|SD file access|미식별|`storage_fopen` string `0x1e680`, SDIO/DMA strings|callable entry/handle ABI/global FS state 미확정|낮음|재사용 불가|
|battery/power|미식별|asset/UI string 단서|ADC/GPIO/charger thresholds 및 callable API 미확정|없음|재사용 불가|

재사용 driver의 현재 상태는 “호출 가능한 실제 API 없음”이다. Phase 3에서 invent된 HAL header 또는 register definition을 만들지 않는다. Ghidra function recovery 후에만, function entry·prototype·global dependency·init predecessor를 한 쌍의 evidence로 등록한다.

