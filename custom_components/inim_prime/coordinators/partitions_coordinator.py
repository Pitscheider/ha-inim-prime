from __future__ import annotations

import logging
from datetime import timedelta
from types import MappingProxyType
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .base_coordinator import InimPrimeBaseCoordinator
from ..gateway import InimPrimeGateway
from ..models.partitions import UnifiedPartition

if TYPE_CHECKING:
    # only imported by the type checker -- never executes at runtime,
    # so this can't participate in a circular import
    from ..runtime_data import InimPrimeConfigEntry

_LOGGER = logging.getLogger(__name__)

class InimPrimePartitionsUpdateCoordinator(InimPrimeBaseCoordinator):
    """Coordinator to fetch partitions from the panel."""

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
            name = "INIM Prime Partitions",
            update_interval = update_interval,
        )

    async def _async_update_data(self) -> MappingProxyType[int, UnifiedPartition]:
        """Fetch data from API."""
        try:
            return await self.gateway.update_partitions()
        except Exception as err:
            raise UpdateFailed(err) from err
