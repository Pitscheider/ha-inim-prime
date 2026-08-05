import logging

from datetime import timedelta
from types import MappingProxyType
from typing import Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from gateway import InimPrimeGateway
from models.zones import UnifiedZone

_LOGGER = logging.getLogger(__name__)

class InimPrimeZonesUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch zones from the panel."""

    def __init__(
            self,
            hass: HomeAssistant,
            update_interval: timedelta,
            entry: ConfigEntry,
            gateway: InimPrimeGateway,
    ):
        super().__init__(
            hass = hass,
            config_entry = entry,
            logger = _LOGGER,
            name = "INIM Prime Zones",
            update_interval = update_interval,
        )
        self.gateway = gateway
        self.entry = entry

    async def _async_update_data(self) -> MappingProxyType[int, UnifiedZone]:
        """Fetch data from API."""
        try:
            return await self.gateway.update_zones()
        except Exception as err:
            raise UpdateFailed(err) from err
