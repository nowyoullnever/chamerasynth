# Kodak Charmera Synth — Phase 7A 최종 보고서

## 결론

원본 펌웨어를 공개 참조에서 다시 받아 크기 2,097,152바이트와 SHA-256 `720ed0b65c91b149b0916498732b0ecf40227736ef5e3c126c487a7b5253436c`를 확인한 뒤 분석했다. 원본과 제3자 참조 저장소는 로컬 ignore 경로에만 존재하며 Git에 추가하지 않았다.

정적으로 검증된 첫 오디오 리소스 교체 범위는 `BEEPWAV`다.

- 리소스 인덱스: source `0x120000`, 0x18-byte entry, 0x200-byte sector.
- BEEP entry: index 4, entry `0x120078`, start sector `0x0f`, 다음 start sector `0x17`.
- BEEP allocation: `0x121e00..0x122dff` (4,096바이트).
- 실제 RIFF/WAVE: `0x121e00..0x122deb` (4,076바이트), PCM mono 11,025 Hz 16-bit, PCM data 4,032바이트.
- padding: 마지막 20바이트가 `0xff`.
- stock selector: `0x1e844(5)`가 `BEEP.WAV` handle slot `+0x0c`를 사용한다.

`tools/phase7a_resource_tool.py`는 위 범위만 허용한다. 같은 길이와 PCM 형식의 저진폭 659.25 Hz tone을 생성했고, 별도 로컬 후보에 적용했다. 후보의 변경 바이트는 3,992개이며 모두 `0x121e00..0x122deb` 안에 있다. 원본 bytes로 복원하면 전체 2 MiB가 byte-identical이다. 후보 SHA-256은 `818f489919c070bccf8d45dc0d95685ad3737dd31ca0b032b6f5f598d2217534`다.

## 질문별 답변

1. **BEEP.WAV의 실제 위치·길이·정렬은?** 위 범위와 0x200 sector 정렬로 확인했다. 이름 lookup과 resource table entry, sector 차이, RIFF header가 서로 일치한다.
2. **원본 컨테이너와 metadata는?** raw RIFF/WAVE PCM이며, index는 name과 sector start를 가진다. BEEP 교체에는 metadata update가 필요하지 않은 동일 길이 방법을 사용했다. checksum/signature 필드는 확인하지 못했다.
3. **SD 리소스 override 경로는?** 미확정이다. 정확한 path/name을 만들거나 SD에 파일을 두지 않았다. resource resolver는 embedded sector table을 읽는 정적 경로만 확인됐다.
4. **버튼 트리거와 PCM은?** BEEP selector 5는 확인했지만 물리 버튼 producer/hook은 미확정이다. PCM backend도 미확정이다. Test B/C는 진행 불가다.
5. **updater와 호환되는가?** 후보가 source header/index/unrelated bytes를 보존한다는 것은 확인했다. 그러나 updater의 altered-image 수락, integrity, target mapping은 미확정이다. flash-ready package는 없다.
6. **실장치 테스트 GO/NO-GO는?** **NO-GO.** 외부 복구 수단과 update acceptance가 증명되지 않았다. stock restore file만으로는 bad boot 뒤 SD updater 진입을 보장하지 못한다.

## 다음 단계 조건

향후 첫 물리 실험은 Test A만 검토 대상으로 남긴다. 그러나 board-compatible SPI 등 외부 복구 read/restore를 실제로 검증하고, updater container/integrity 조건을 확인하고, 희생 장치·안정 전원·명시적 단일 설치 권한을 갖춘 뒤에만 별도 Phase에서 판단한다. 이 Phase에서는 장치 연결, microSD 설치, USB 명령, flash write를 전혀 수행하지 않았다.
