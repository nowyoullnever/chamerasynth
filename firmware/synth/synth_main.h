#ifndef CHAMERA_SYNTH_MAIN_H
#define CHAMERA_SYNTH_MAIN_H

#include "../hal/audio_hal.h"

typedef struct SynthApplication {
    AudioHal *audio;
    bool active;
} SynthApplication;

AudioHalResult synth_application_start(SynthApplication *application);
AudioHalResult synth_application_submit(SynthApplication *application, const AudioHalPcmBuffer *buffer);
AudioHalResult synth_application_stop(SynthApplication *application);
void synth_application_shutdown(SynthApplication *application);

#endif
