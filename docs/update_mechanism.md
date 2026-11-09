# SD 업데이트 메커니즘 조사

## 확정된 파일 사실

- Original_Firmware는 `0x0218ac`에 `C:\\JH_`, `0x0218c4`에 `202505201029`, `0x020e38`에 `Upgrade` string을 가진다. 이것은 image가 SD update UI/filename을 언급함을 보인다.
- Keychain Camera Plus (KCP) commit `209c25a47ce91c805b663edb6e18861b367a5a1b`의 `scripts/pack_sd_firmware.py:31-68`는 **자체 구현/주장**으로 `JH_5408<YYYYMMDDhhmm>_<CHECKSUM8HEX>.bin`와 `sum(data) & 0xffffffff`를 정의한다. 이는 암호학적 checksum이 아니다.
- KCP stock file은 2 MiB이고 30 block (`0x1e0000`) prefix의 byte sum은 filename checksum `0x0f065d55`와 일치한다. KCP UVC file은 3 bytes (`0x22124`, `0x22126`, `0x22127`)가 다르고 sum `0x0f065eb9`다.
- KCP stock과 Sirius dump는 update 인접 영역 `0x21380..0x21880`가 동일하지만 전체는 약 76,034 bytes 다르다. 따라서 KCP stock을 이 Sirius unit의 복구 image로 간주할 수 없다.

## 주장과 검증 상태

|질문|현재 결론|근거/한계|
|---|---|---|
|`JH_5408` filename|형식은 강한 후보|Sirius 문자열 + KCP parser. Original A32 updater의 disassembly가 없어 parser semantics 미확정|
|timestamp check|후보|KCP는 index 7–18 / stock timestamp 회피를 구현한다. 원본 code 검증 필요|
|checksum|후보|KCP byte sum 및 배포 file sum은 일치한다. Original code compare를 아직 하지 못함|
|FAT/root scan|후보|KCP guide 주장, Sirius `C:\\JH_` string. FAT API/control flow를 아직 확인 못함|
|erase/write/verify|미확정|KCP 문서는 write 및 verify를 주장하지만 원본 updater routine decompilation/실기기 readback 없음|
|2 MiB wraparound|미확정 위험|KCP `pack_sd_firmware.py:13-28`의 `end+0x10000` 및 21-bit wrap 산술은 맞지만, target offset formula, chip addressing, erase opcode가 원본에서 미검증|
|30-block workaround|안전하다고 말할 수 없음|`0x1e0000+0x10000=0x1f0000` 산술만 확정. KCP script는 tail이 non-FF여도 잘라낸다 (`:79-88`)—일반적으로 안전하지 않다|
|updater 자체 overwrite|미확정|erase/write 범위와 executing-from-RAM 여부 모두 미확정|
|SD direct execute|증거 없음|업데이트 파일 검색은 flash-write path의 단서일 뿐 execute-from-SD를 보이지 않는다|
|secondary RAM loader|증거 없음|Project-Sirius issue #1의 관련 SDK 언급은 Charmera 구현 증거가 아니다|

Project-Sirius roadmap은 SD boot를 미래 목표로 적고 있으며, 댓글의 update/brick 이야기는 제3자 보고다. 이는 연구 방향의 단서일 뿐 안전성 증거가 아니다. 출처: [roadmap](https://www.reddit.com/r/CharmeraModding/comments/1u6v638/project_sirius_roadmap/), [issue #1](https://github.com/Khimira/Project-Sirius/issues/1).

## Phase 1 결론

SD update는 **flash를 바꾸는 것으로 보이는 고위험 경로**이며, 이 프로젝트에서는 절대 실행하지 않는다. SD application loader는 설계 후보일 수 있으나 현재 실현 가능성을 주장할 근거가 없다.

