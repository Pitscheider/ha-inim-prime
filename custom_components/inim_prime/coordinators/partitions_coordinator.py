import logging
from datetime import timedelta
from typing import Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from inim.prime.primelan.client import InimPrimeClient
from inim.prime.primelan.models.partition import PartitionStatus

_LOGGER = logging.getLogger(__name__)

class InimPrimePartitionsUpdateCoordinator(DataUpdateCoordinator[Dict[int, PartitionStatus]]):
    """Coordinator to fetch partitions from the panel."""

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
            name = "INIM Prime Partitions",
            update_interval = update_interval,
        )
        self.client = client
        self.data: Dict[int, PartitionStatus] = {}  # just an empty dict
        self.entry = entry

    async def _async_update_data(self) -> Dict[int, PartitionStatus]:
        """Fetch data from API."""
        try:
            partitions = await self.client.get_partitions_status()

            self.data = partitions

            return self.data
        except Exception as err:
            raise UpdateFailed(err) from err
