#include "audio_hal.h"

static bool has_required_operations(const AudioHal *hal) {
    return hal != NULL && hal->ops != NULL && hal->ops->initialize != NULL &&
           hal->ops->submit_pcm != NULL && hal->ops->start != NULL &&
           hal->ops->stop != NULL && hal->ops->state != NULL &&
           hal->ops->release_pcm != NULL;
}

AudioHalResult audio_hal_initialize(AudioHal *hal) {
    if (!has_required_operations(hal)) {
        return AUDIO_HAL_INVALID_ARGUMENT;
    }
    AudioHalResult result = hal->ops->initialize(hal->backend_context);
    hal->initialized = result == AUDIO_HAL_OK;
    return result;
}

AudioHalResult audio_hal_submit_pcm(AudioHal *hal, const AudioHalPcmBuffer *buffer) {
    if (!has_required_operations(hal) || buffer == NULL || buffer->data == NULL ||
        buffer->byte_count == 0) {
        return AUDIO_HAL_INVALID_ARGUMENT;
    }
    if (!hal->initialized) {
        return AUDIO_HAL_NOT_INITIALIZED;
    }
    return hal->ops->submit_pcm(hal->backend_context, buffer);
}

AudioHalResult audio_hal_start(AudioHal *hal) {
    if (!has_required_operations(hal)) {
        return AUDIO_HAL_INVALID_ARGUMENT;
    }
    if (!hal->initialized) {
        return AUDIO_HAL_NOT_INITIALIZED;
    }
    return hal->ops->start(hal->backend_context);
}

AudioHalResult audio_hal_stop(AudioHal *hal) {
    if (!has_required_operations(hal)) {
        return AUDIO_HAL_INVALID_ARGUMENT;
    }
    if (!hal->initialized) {
        return AUDIO_HAL_NOT_INITIALIZED;
    }
    return hal->ops->stop(hal->backend_context);
}

AudioHalState audio_hal_state(const AudioHal *hal) {
    if (!has_required_operations(hal) || !hal->initialized) {
        return AUDIO_HAL_STOPPED;
    }
    return hal->ops->state(hal->backend_context);
}

AudioHalResult audio_hal_release_pcm(AudioHal *hal, uint32_t token) {
    if (!has_required_operations(hal)) {
        return AUDIO_HAL_INVALID_ARGUMENT;
    }
    if (!hal->initialized) {
        return AUDIO_HAL_NOT_INITIALIZED;
    }
    return hal->ops->release_pcm(hal->backend_context, token);
}
