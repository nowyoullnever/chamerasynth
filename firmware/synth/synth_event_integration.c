#include "synth_event_integration.h"

SynthEventResult synth_event_handle_inner(
    const SynthEventIntegration *integration,
    uint32_t code,
    const void *payload,
    size_t payload_size) {
    if (integration == NULL || integration->publish_outer == NULL) {
        return SYNTH_EVENT_INVALID_CONFIGURATION;
    }
    if (code == SYNTH_INNER_UPDATE_REQUEST) {
        if (!integration->publish_outer(integration->context, SYNTH_OUTER_UPDATER_EVENT)) {
            return SYNTH_EVENT_PUBLISH_FAILED;
        }
        if (integration->shutdown_application != NULL) {
            integration->shutdown_application(integration->context);
        }
        return SYNTH_EVENT_RETURN_FOR_STOCK_CLEANUP;
    }
    if (integration->handle_application_event != NULL) {
        integration->handle_application_event(integration->context, code, payload, payload_size);
    }
    return SYNTH_EVENT_CONTINUE;
}
