# Phase 1 펌웨어 식별 보고서

## 범위와 판정 규칙

이 문서는 로컬 파일을 읽기만 한 정적 분석 결과다. 카메라 연결, USB/vendor 명령, SPI 쓰기, SD 카드 갱신은 수행하지 않았다. `관찰`은 파일 또는 출처에서 직접 확인한 사실이고, `추론`은 후속 검증이 필요한 해석이다. 파일 오프셋은 런타임 주소가 아니다.

## 대상 식별

|항목|값|근거|
|---|---|---|
|파일|`references/Project-Sirius/Original_Firmware.bin`|Project-Sirius commit `8d64da5ca8ab0f1cff06f99a3488ca01afba17b2`|
|크기|2,097,152 bytes (`0x200000`, 2 MiB)|파일 메타데이터, 헤더 LE word `0x000008 = 0x00200000`|
|SHA-256|`720ed0b65c91b149b0916498732b0ecf40227736ef5e3c126c487a7b5253436c`|`tools/inspect_firmware.py` 출력|
|끝의 erased 영역|`0x1aee00..0x1fffff`가 `0xff`|직접 바이트 스캔|

`0x200000` 크기, 헤더의 동일 크기값, erased tail은 **2 MiB SPI 주소공간 전체를 덤프한 파일과 일치**한다. 그러나 flash chip 표기·읽기 절차·반복 readback이 없으므로 “완전한 물리 SPI dump”라고 확정할 수는 없다.

## 컨테이너와 실행 코드

### 관찰

- `0x000000`: ASCII `SPII`.
- `0x000004`: LE `0x30000200`, `0x000008`: LE `0x00200000`, `0x000014`: ASCII `SRIy`.
- `0x000020..0x000047`에는 `d0667802`, `00000005`, `d0000088`, `0000a12b`, `d000008c`, `00002495`, `d0000028`, `00008005`, `d00000ac`, `00000104` LE words가 있다.
- `0x000200`부터 ARM vector 형태가 있다: `E59FF018` 5개, `EAFFFFFE` (무한 branch), `E59FF014` 2개. vector literal 대상 `0x000220..0x000238`은 `0x3c, 0x168, 0x174, 0x180, 0x18c, 0x198, 0x1c8`이다.
- reset 후보 `0x00023c`의 첫 명령은 `E32FF0D3` (`MSR CPSR_c,#0xd3`)이며, 이어서 A32 `LDR/STR` MMIO 쓰기를 수행한다. 대상의 LSB가 0이고 명령 폭이 32 bit이므로 이 시작 영역은 little-endian **ARM A32 state**다. Thumb 실행 증거는 이 경로에서 없다.

### 추론 및 한계

`SPII/SRIy`는 Generalplus 계열 도구 설정에서도 SPI-NOR header tag로 쓰인다 (`references/ZTKVR/tool/G+CodePacker 1.0.9.27/PackConfig/GPL329XX/SPINOR.ini:10-19`). 하지만 ZTKVR은 다른 GPL326XXB 대상이다. 따라서 이 파일이 **독점 SPII/SRIy 컨테이너**라는 식별까지만 확정하며, 위 헤더 word의 partition·주소·checksum 의미는 미확정이다.

payload를 논리 주소 0에 mapping한다고 가정하면 vector reset target `0x3c`가 file `0x23c`와 맞는다. 이는 유력한 mapping 가설일 뿐 BootROM 문서가 없으므로 확정 runtime address가 아니다.

## 초기화와 entry 후보

|관찰|근거|해석/신뢰도|
|---|---|---|
|초기 MMIO store|`0x24c..0x290`; literals `0x3e0=0xd0100038`, `0x3e4=0xd0300000`, `0x3e8/3ec/3f0=0xd0300040/80/c0`, `0x3f4=0xd05001fc`, `0x3f8=0xd07023c0`|MMIO 접근은 높음; clock/DDR/peripheral 명칭은 미확정|
|zero loop 후보|`0x294..0x2dc`; literals `0x408=0x0010af30`, `0x40c=0x000a3820`|논리 mapping 가정 시 BSS-like `0x0010af30..0x001ae74f` zeroing 추론, 중간|
|예외 mode stack|`0x2e0+`: CPSR mode `D2,D1,D7,DB,DF,D3`, `E1A0D002`|IRQ/FIQ/abort/undefined/system/supervisor stack 초기화는 높음; stack 주소/크기는 미확정|
|bootstrap/main 후보|`0x364: EA00B677` → `0x2dd48`; 시작 `E92D401C`, calls to `0x31264`, `0x36254`, `0x8cf28`, `0x2c610`, `0x3626c`|branch/호출은 관찰, 이것이 application main인 것은 중간 추론|

## 데이터·리소스·버전 문자열

- `GPZP` marker 79개, 예: `0x0629e`; resource index가 `0x12001f`부터 밀집한다. JPEG SOI 예: `0x0ffb78`, `0x120800`, `0x180000`; RIFF 예: `0x080340`, `0x121e00`, `0x162400`.
- ZIP `PK` container는 발견되지 않았다. GPZP의 압축 알고리즘은 확인하지 못했다. zlib-like byte signature도 컨테이너 증거가 아니다.
- build/naming 단서: `Generplus` `0x00bca8`; `JH5408  20250520` `0x018964`; `D.WH5408`/`241128` `0x01f0e4`/`0x01f0f4`; `202505201029` `0x0218c4`.

문자열은 build context의 단서일 뿐 SoC 모델, board revision 또는 기능 동작의 증명은 아니다.

## 재현

```powershell
python tools/inspect_firmware.py references/Project-Sirius/Original_Firmware.bin --json work/firmware-inspection.json
python -m unittest discover -s tests -v
```

REA의 firmware-region scanner는 이 Windows 환경에서 Linux/Binwalk가 필요해 실행되지 않았고, raw bin은 configured Ghidra importer가 수락하지 않았다. 따라서 본 문서는 raw-byte 정적 분석이며 Ghidra decompilation 결과를 주장하지 않는다.

