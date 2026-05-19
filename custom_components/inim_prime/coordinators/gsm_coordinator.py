import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from inim.prime.primelan.client import InimPrimeClient
from inim.prime.primelan.models.gsm import GSMSStatus

_LOGGER = logging.getLogger(__name__)

class InimPrimeGSMUpdateCoordinator(DataUpdateCoordinator[GSMSStatus]):
    """Coordinator to fetch GSM from the panel."""

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
            name = "INIM Prime GSM",
            update_interval = update_interval,
        )
        self.client = client
        self.data: GSMSStatus = GSMSStatus(
            supply_voltage = None,
            firmware_version = None,
            operator = None,
            signal_strength = None,
            credit = None,
        )
        self.entry = entry

    async def _async_update_data(self) -> GSMSStatus:
        """Fetch data from API."""
        try:
            gsm = await self.client.get_gsm_status()

            self.data = gsm

            return self.data
        except Exception as err:
            raise UpdateFailed(err) from err
