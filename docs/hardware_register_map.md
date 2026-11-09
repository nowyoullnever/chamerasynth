# 하드웨어 추적 표

아래 주소는 Charmera register 정의가 아니다. `문자열`은 해당 기능을 가진 코드/서비스가 image 안에 존재한다는 낮은 수준의 근거다. 함수 시작 주소가 아니며, MMIO label을 추정하지 않는다.

|영역|후보 함수/문자열 또는 register|파일 오프셋/주소|근거|신뢰도|의존성·추가 검증|
|---|---|---|---|---|---|
|LCD/display|`ap_display_init`|`0x0166fc`|ASCII string|낮음|call xref, framebuffer format/stride 및 LCD bus write cluster 필요|
|LCD/video decode|`Disp_Mjpeg_Init`|`0x0106c8`|ASCII string|낮음|display init과의 call relation, frame buffer allocation 필요|
|buttons/GPIO|미식별|—|public GPCV2247F page는 GPIO를 열거하지만 image에서 key handler와 MMIO relation을 확정하지 못함|없음|GPIO read/poll/IRQ cluster 및 board pin mapping 필요|
|microSD/FAT|`storage_fopen`, `C:\\DCIM`, `C:\\SPIDCIM`|`0x01e680`, `0x002dbc`, `0x0030f8` 부근|파일 API/name strings|낮음|SD CMD/response loop, 512-byte DMA, filesystem call xref 필요|
|SDIO/SD DMA|`sdio_allocate_dma_buffer`, `sdio_free_dma_buffer`, `gm_sdc_api_sdio_cmd52 ret = %d`|`0x07b254`, `0x07b320`, `0x07b064`|ASCII string|낮음|SDIO가 이 board에서 microSD path인지와 controller/MMIO/descriptor xref 필요|
|SD GPIO/IRQ|`Setup SDIO GPIO rx int`, `sdio_if_irq_enable`|`0x0bf3f8`, `0x0bdf38`|ASCII string|낮음|GPIO number, interrupt number, board connection 모두 미확정|
|SPI flash|`nvspiflash_retrieval`, `nvmemory_rs_byte_load`|`0x001b70`, `0x0016a8`|ASCII string|낮음|SPI command/WREN/erase/program/poll code, flash chip ID/readback 필요|
|audio playback/DAC|`CLICK.WAV`, `POWERON_AUDIO.WAV`, `BEEP.WAV`|`0x01e494` onward|embedded cue names|낮음|PCM buffer/DMA/FIFO/IRQ path 및 DAC register contract 필요|
|DMA|early literal `0xd07023c0`; `dma` strings|store `0x288..0x290`; strings `0x07b262+`|reset MMIO store/string|낮음|literal uses + transfer descriptor loops 필요|
|battery/power|`BATTERY00.GPZP`, battery strings|`0x006294`, `0x120060`, `0x141dc2`|resource/text only|낮음|ADC/GPIO/power event code 및 calibrated measurements 필요|
|USB|`drv_l2_usbd_msdc_init`|`0x02a304`|ASCII driver-name string|낮음|USB descriptor/endpoint/MMIO xrefs 필요|
|USB/DMA/IRQ|`drv_l1_usbd_enable_isr ok`, `USBD_BULKAB_OUT_M_DMA_AB_DONE_EVENT`, `GENPLUS USB-MSDC DISK A 1.00`|`0x08a458`, `0x088b88`, `0x0f3ce4`|ASCII strings/descriptor|낮음|endpoint setup, ISR/descriptor control-flow 및 physical enumeration 필요|
|camera ISP (신스에 비핵심)|`drv_l2_cdsp_open`|`0x06a3e0`|ASCII string|낮음|CDSP block과 sensor pin/clock을 확인해야 함|
|generic early MMIO|unlabelled addresses|`0xd0100038`, `0xd0300000/40/80/c0`, `0xd05001fc`, `0xd07023c0`|reset stores `0x24c..0x290`|중간 (access만)|GPCV2247F 전용 SFR map 또는 control-flow/data-flow corroboration 필요|

## 규칙

1. Charmera label은 **MMIO access pattern + call context/상수/독립 근거** 두 개 이상이 맞을 때만 추가한다.
2. ZTKVR의 GPL326XXB SFR 예: GPIO `0xc000…`, DAC `0xc00d0000`, SD `0xc00a0000`은 Charmera 주소가 아니다 (`references/ZTKVR/driver_l1/inc/drv_l1_sfr.h`).
3. 작동 driver, pin, interrupt 번호, battery threshold, LCD timing은 Phase 1에서 확인되지 않았다.

