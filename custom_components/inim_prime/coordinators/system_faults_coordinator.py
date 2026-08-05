import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from gateway import InimPrimeGateway
from models.system_faults import UnifiedSystemFaults

_LOGGER = logging.getLogger(__name__)

class InimPrimeSystemFaultsUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch system faults from the panel."""

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
            name = "INIM Prime System Faults",
            update_interval = update_interval,
        )
        self.gateway = gateway
        self.entry = entry

    async def _async_update_data(self) -> UnifiedSystemFaults:
        """Fetch data from API."""
        try:
            return await self.gateway.update_system_faults()
        except Exception as err:
            raise UpdateFailed(err) from err
