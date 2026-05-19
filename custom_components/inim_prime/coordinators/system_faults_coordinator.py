import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from inim.prime.primelan.client import InimPrimeClient
from inim.prime.primelan.models.system_faults import SystemFaultsStatus

_LOGGER = logging.getLogger(__name__)

class InimPrimeSystemFaultsUpdateCoordinator(DataUpdateCoordinator[SystemFaultsStatus]):
    """Coordinator to fetch system faults from the panel."""

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
            name = "INIM Prime System Faults",
            update_interval = update_interval,
        )
        self.client = client
        self.data: SystemFaultsStatus = SystemFaultsStatus(
            supply_voltage = None,
            faults = frozenset(),
        )
        self.entry = entry

    async def _async_update_data(self) -> SystemFaultsStatus:
        """Fetch data from API."""
        try:
            system_faults = await self.client.get_system_faults_status()

            self.data = system_faults

            return self.data
        except Exception as err:
            raise UpdateFailed(err) from err
