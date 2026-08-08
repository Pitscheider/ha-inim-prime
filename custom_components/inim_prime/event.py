from .entities.panel import PanelLogEventsEvent
from .custom_types import InimPrimeConfigEntry

async def async_setup_entry(hass, entry: InimPrimeConfigEntry, async_add_entities) -> None:
    panel_log_events_coordinator = entry.runtime_data.coordinators.panel_log_events

    entities = []

    if panel_log_events_coordinator is not None:
        panel_log_events_event = PanelLogEventsEvent(panel_log_events_coordinator, entry)
        panel_log_events_coordinator.panel_log_events_entity = panel_log_events_event

        entities.append(panel_log_events_event)

    async_add_entities(entities, update_before_add = True)
