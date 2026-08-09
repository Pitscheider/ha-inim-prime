from datetime import timedelta

from homeassistant.core import HomeAssistant, _LOGGER
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..gateway import InimPrimeGateway
from ..runtime_data import InimPrimeConfigEntry
from ..entry_data import InimPrimeConfigData, InimPrimeOptionsData, get_entry_data, get_entry_options


class InimPrimeBaseCoordinator(DataUpdateCoordinator):
    """Common init for all INIM Prime coordinators: stores the gateway and
    typed, cached views of entry.data / entry.options.

    Caching (rather than calling get_entry_data/get_entry_options on every
    access) relies on both entry.data and entry.options changes always
    triggering a full entry reload -- which recreates coordinators from
    scratch -- rather than mutating them in place on a live entry.
    """
    entry_data: InimPrimeConfigData
    entry_options: InimPrimeOptionsData

    def __init__(
            self,
            hass: HomeAssistant,
            update_interval: timedelta,
            entry: InimPrimeConfigEntry,
            gateway: InimPrimeGateway,
            name: str,
    ):
        super().__init__(
            hass = hass,
            config_entry = entry,
            logger = _LOGGER,
            name = name,
            update_interval = update_interval,
        )
        self.gateway = gateway
        self.entry_data = get_entry_data(entry)
        self.entry_options = get_entry_options(entry)

    @property
    def serial_number(self) -> str:
        return self.entry_data["serial_number"]