#include "synth_main.h"

AudioHalResult synth_application_start(SynthApplication *application) {
    if (application == NULL || application->audio == NULL) {
        return AUDIO_HAL_INVALID_ARGUMENT;
    }
    AudioHalResult result = audio_hal_initialize(application->audio);
    if (result != AUDIO_HAL_OK) {
        return result;
    }
    result = audio_hal_start(application->audio);
    application->active = result == AUDIO_HAL_OK;
    return result;
}

AudioHalResult synth_application_submit(SynthApplication *application, const AudioHalPcmBuffer *buffer) {
    if (application == NULL || !application->active) {
        return AUDIO_HAL_NOT_INITIALIZED;
    }
    return audio_hal_submit_pcm(application->audio, buffer);
}

AudioHalResult synth_application_stop(SynthApplication *application) {
    if (application == NULL || application->audio == NULL) {
        return AUDIO_HAL_INVALID_ARGUMENT;
    }
    AudioHalResult result = audio_hal_stop(application->audio);
    if (result == AUDIO_HAL_OK) {
        application->active = false;
    }
    return result;
}

void synth_application_shutdown(SynthApplication *application) {
    if (application == NULL || application->audio == NULL) {
        return;
    }
    if (application->active) {
        (void)audio_hal_stop(application->audio);
        application->active = false;
    }
}
