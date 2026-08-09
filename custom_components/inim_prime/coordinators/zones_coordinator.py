from __future__ import annotations

import logging
from datetime import timedelta
from types import MappingProxyType
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .base_coordinator import InimPrimeBaseCoordinator
from ..gateway import InimPrimeGateway
from ..models.zones import UnifiedZone

if TYPE_CHECKING:
    # only imported by the type checker -- never executes at runtime,
    # so this can't participate in a circular import
    from ..runtime_data import InimPrimeConfigEntry

_LOGGER = logging.getLogger(__name__)

class InimPrimeZonesUpdateCoordinator(InimPrimeBaseCoordinator):
    """Coordinator to fetch zones from the panel."""

    def __init__(
            self,
            hass: HomeAssistant,
            update_interval: timedelta,
            entry: InimPrimeConfigEntry,
            gateway: InimPrimeGateway,
    ):
        super().__init__(
            hass = hass,
            entry = entry,
            gateway = gateway,
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
