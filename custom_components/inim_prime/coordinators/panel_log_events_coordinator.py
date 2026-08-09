from __future__ import annotations

import logging
from datetime import timedelta
from typing import List, TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..entry_data import get_entry_options, get_entry_data
from ..const import (
    DOMAIN,
    STORAGE_KEY_LAST_PANEL_EVENT_LOGS,
    PANEL_LOG_EVENTS_FETCH_LIMIT_TRIGGER,
    PANEL_LOG_EVENTS_FETCH_LIMIT_MAX,
)
from ..gateway import InimPrimeGateway
from ..helpers.panel_log_events import (
    deserialize_panel_log_events,
    serialize_panel_log_events,
    async_fetch_panel_log_events,
)
from ..models.log_events import UnifiedLogEvent

if TYPE_CHECKING:
    # only imported by the type checker -- never executes at runtime,
    # so this can't participate in a circular import
    from ..runtime_data import InimPrimeConfigEntry

_LOGGER = logging.getLogger(__name__)


class InimPrimePanelLogEventsCoordinator(DataUpdateCoordinator):
    # Coordinator to fetch panel log events independently.
    STORAGE_VERSION = 1
    panel_log_events_entity = None
    last_panel_log_events: list[UnifiedLogEvent] = []
    panel_log_events_fetch_limit: int

    def __init__(
            self,
            hass: HomeAssistant,
            update_interval: timedelta,
            entry: InimPrimeConfigEntry,
            gateway: InimPrimeGateway,
            panel_log_events_fetch_limit: int,
    ):
        super().__init__(
            hass = hass,
            config_entry = entry,
            logger = _LOGGER,
            name = "INIM Prime Panel Log Events",
            update_interval = update_interval,
        )
        self.gateway = gateway
        data = get_entry_data(entry)
        self.panel_log_events_fetch_limit = panel_log_events_fetch_limit

        self.last_panel_log_events_store = Store(
            hass,
            self.STORAGE_VERSION,
            f"{DOMAIN}_{data["serial_number"]}_{STORAGE_KEY_LAST_PANEL_EVENT_LOGS}",
        )


    async def _async_update_data(self):
        try:
            # Do not consume panel log events until panel_log_events_entity is ready,
            # otherwise events could be lost before HA can fire them.
            if self.panel_log_events_entity:

                # Phase 1: lightweight "trigger" fetch.
                # Fetch only a small number of the most recent log events to quickly check
                # whether any new events appeared since the last poll.
                #
                # - `self.last_panel_log_events` is used to filter out already known events
                # - The fetched list is not stored; we only check if there are any new events
                # - If no new events are detected here, the heavier full fetch is skipped
                _, trigger_new_events = await async_fetch_panel_log_events(
                    last_panel_log_events = self.last_panel_log_events,
                    gateway = self.gateway,
                    limit = PANEL_LOG_EVENTS_FETCH_LIMIT_TRIGGER,
                )

                # If at least one new event is detected, perform a full fetch to ensure
                # we do not miss any events that occurred between polling intervals.
                if trigger_new_events:

                    # Phase 2: authoritative fetch.
                    # Fetch a larger window of recent log events and re-filter them against
                    # the last known state to obtain the complete and correctly ordered list of new events.
                    current_panel_log_events, current_panel_log_events_filtered = await async_fetch_panel_log_events(
                        last_panel_log_events = self.last_panel_log_events,
                        gateway = self.gateway,
                        limit = self.panel_log_events_fetch_limit,
                    )

                    # Defensive max-limit fetch:
                    # If the fetched window is fully saturated with new events, it may mean
                    # more events occurred than the configured fetch limit. Perform a single
                    # refetch using the maximum allowed window to reduce the risk of missing events.
                    if (
                            self.panel_log_events_fetch_limit < PANEL_LOG_EVENTS_FETCH_LIMIT_MAX and
                            self.panel_log_events_fetch_limit == len(current_panel_log_events_filtered)
                    ):
                        current_panel_log_events, current_panel_log_events_filtered = await async_fetch_panel_log_events(
                            last_panel_log_events = self.last_panel_log_events,
                            gateway = self.gateway,
                            limit = PANEL_LOG_EVENTS_FETCH_LIMIT_MAX,
                        )

                    # If there are any new events after filtering
                    if current_panel_log_events_filtered:
                        # Pass the new events to the panel_log_events_entity to trigger HA events.
                        # This will fire each event in PanelLogEventsEvent.
                        await self.panel_log_events_entity.handle_events(
                            current_panel_log_events_filtered,
                        )

                        # Update the stored full list of panel events and persist it.
                        # Since there are new events, we are sure `current_panel_log_events` contains valid data.
                        self.last_panel_log_events = current_panel_log_events
                        await self.async_save_current_panel_log_events(
                            self.last_panel_log_events,
                        )
        except Exception as err:
            raise UpdateFailed(err) from err

        return

    async def async_load_last_panel_log_events(self):
        """Load logs from HA storage."""
        stored_data = await self.last_panel_log_events_store.async_load()
        if stored_data and "logs" in stored_data:
            last_panel_log_events = deserialize_panel_log_events(stored_data["logs"])
        else:
            last_panel_log_events = []
        return last_panel_log_events

    async def async_save_current_panel_log_events(
            self,
            current_panel_log_events: List[UnifiedLogEvent]
    ):
        if current_panel_log_events:
            await self.last_panel_log_events_store.async_save(
                {"logs": serialize_panel_log_events(current_panel_log_events)}
            )

    async def async_startup(self) -> None:
        """Load persisted data before first refresh."""
        self.last_panel_log_events = await self.async_load_last_panel_log_events()
