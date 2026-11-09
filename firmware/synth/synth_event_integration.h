#ifndef CHAMERA_SYNTH_EVENT_INTEGRATION_H
#define CHAMERA_SYNTH_EVENT_INTEGRATION_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Observed logical event values; their runtime queue ABI is unresolved. */
enum {
    SYNTH_OUTER_APPLICATION_EVENT = 0x100,
    SYNTH_OUTER_UPDATER_EVENT = 0x108,
    SYNTH_INNER_UPDATE_REQUEST = 0x5025
};

typedef bool (*SynthPublishOuterEvent)(void *context, uint32_t code);
typedef void (*SynthApplicationEvent)(void *context, uint32_t code, const void *payload, size_t payload_size);
typedef void (*SynthApplicationShutdown)(void *context);

typedef struct SynthEventIntegration {
    void *context;
    SynthPublishOuterEvent publish_outer;
    SynthApplicationEvent handle_application_event;
    SynthApplicationShutdown shutdown_application;
} SynthEventIntegration;

typedef enum SynthEventResult {
    SYNTH_EVENT_CONTINUE = 0,
    /* Caller must retain stock cleanup/return semantics after this result. */
    SYNTH_EVENT_RETURN_FOR_STOCK_CLEANUP,
    SYNTH_EVENT_PUBLISH_FAILED,
    SYNTH_EVENT_INVALID_CONFIGURATION
} SynthEventResult;

SynthEventResult synth_event_handle_inner(
    const SynthEventIntegration *integration,
    uint32_t code,
    const void *payload,
    size_t payload_size);

#endif
