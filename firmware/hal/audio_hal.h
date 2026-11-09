#ifndef CHAMERA_SYNTH_AUDIO_HAL_H
#define CHAMERA_SYNTH_AUDIO_HAL_H

/*
 * Hardware-neutral audio boundary for the future synth application.
 *
 * This is not a recovered Charmera driver ABI.  A target adapter may be added
 * only after the firmware playback service and its calling convention have
 * been recovered.  No MMIO register, firmware address, or assumed audio
 * format appears in this interface.
 */

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef enum AudioHalResult {
    AUDIO_HAL_OK = 0,
    AUDIO_HAL_INVALID_ARGUMENT,
    AUDIO_HAL_NOT_INITIALIZED,
    AUDIO_HAL_BACKEND_REJECTED,
    AUDIO_HAL_UNSUPPORTED
} AudioHalResult;

typedef enum AudioHalState {
    AUDIO_HAL_STOPPED = 0,
    AUDIO_HAL_RUNNING,
    AUDIO_HAL_FAULT
} AudioHalState;

typedef struct AudioHalPcmBuffer {
    const void *data;
    size_t byte_count;
    uint32_t token;
} AudioHalPcmBuffer;

/*
 * On AUDIO_HAL_OK from submit_pcm(), the backend owns the descriptor and PCM
 * storage until release_pcm() is invoked for the same token. The caller must
 * keep that storage immutable and alive in the interim.  Rejected buffers
 * remain caller-owned. The contract deliberately leaves sample rate, channel
 * count, and sample representation unresolved for the target adapter.
 */
typedef struct AudioHalBackendOps {
    AudioHalResult (*initialize)(void *context);
    AudioHalResult (*submit_pcm)(void *context, const AudioHalPcmBuffer *buffer);
    AudioHalResult (*start)(void *context);
    AudioHalResult (*stop)(void *context);
    AudioHalState (*state)(void *context);
    AudioHalResult (*release_pcm)(void *context, uint32_t token);
} AudioHalBackendOps;

typedef struct AudioHal {
    const AudioHalBackendOps *ops;
    void *backend_context;
    bool initialized;
} AudioHal;

AudioHalResult audio_hal_initialize(AudioHal *hal);
AudioHalResult audio_hal_submit_pcm(AudioHal *hal, const AudioHalPcmBuffer *buffer);
AudioHalResult audio_hal_start(AudioHal *hal);
AudioHalResult audio_hal_stop(AudioHal *hal);
AudioHalState audio_hal_state(const AudioHal *hal);
AudioHalResult audio_hal_release_pcm(AudioHal *hal, uint32_t token);

#endif
