import logging

from datetime import timedelta
from typing import Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from inim.prime.primelan.client import InimPrimeClient
from inim.prime.primelan.models.zone import ZoneStatus

_LOGGER = logging.getLogger(__name__)

class InimPrimeZonesUpdateCoordinator(DataUpdateCoordinator[Dict[int, ZoneStatus]]):
    """Coordinator to fetch zones from the panel."""

    def __init__(
            self,
            hass: HomeAssistant,
            update_interval: timedelta,
            entry: ConfigEntry,
            client: InimPrimeClient,
    ):
        super().__init__(
            hass = hass,
            config_entry = entry,
            logger = _LOGGER,
            name = "INIM Prime Zones",
            update_interval = update_interval,
        )
        self.client = client
        self.data: Dict[int, ZoneStatus] = {}  # just an empty dict
        self.entry = entry

    async def _async_update_data(self) -> Dict[int, ZoneStatus]:
        """Fetch data from API."""
        try:
            zones = await self.client.get_zones_status()

            self.data = zones

            return self.data
        except Exception as err:
            raise UpdateFailed(err) from err
