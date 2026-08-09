from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .base_coordinator import InimPrimeBaseCoordinator
from ..gateway import InimPrimeGateway
from ..models.gsm import UnifiedGSM

if TYPE_CHECKING:
    # only imported by the type checker -- never executes at runtime,
    # so this can't participate in a circular import
    from ..runtime_data import InimPrimeConfigEntry

_LOGGER = logging.getLogger(__name__)

class InimPrimeGSMUpdateCoordinator(InimPrimeBaseCoordinator):
    """Coordinator to fetch GSM from the panel."""

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
            name = "INIM Prime GSM",
            update_interval = update_interval,
        )


    async def _async_update_data(self) -> UnifiedGSM:
        """Fetch data from API."""
        try:
            return await self.gateway.update_gsm()
        except Exception as err:
            raise UpdateFailed(err) from err
