from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from .coordinators import (
    InimPrimeZonesUpdateCoordinator,
    InimPrimePartitionsUpdateCoordinator,
    InimPrimeGSMUpdateCoordinator,
    InimPrimeSystemFaultsUpdateCoordinator,
    InimPrimePanelLogEventsCoordinator,
)

from .gateway import InimPrimeGateway


@dataclass
class InimPrimeCoordinators:
    """Coordinators for this entry, typed per-feature instead of string-keyed.

    zones / partitions always exist. The PrimeLAN-only ones are None on a
    native-only entry -- platforms check for None instead of doing
    dict.get(SOME_STRING_KEY).
    """
    zones: InimPrimeZonesUpdateCoordinator | None = None
    partitions: InimPrimePartitionsUpdateCoordinator | None = None
    gsm: InimPrimeGSMUpdateCoordinator | None = None
    system_faults: InimPrimeSystemFaultsUpdateCoordinator | None = None
    panel_log_events: InimPrimePanelLogEventsCoordinator | None = None

    def all(self) -> list:
        """All coordinators that exist, for shutdown/iteration."""
        return [
            c for c in (
                self.zones, self.partitions, self.gsm,
                self.system_faults, self.panel_log_events,
            ) if c is not None
        ]

@dataclass
class InimPrimeRuntimeData:
    serial_number: str
    gateway: InimPrimeGateway
    coordinators: InimPrimeCoordinators

type InimPrimeConfigEntry = ConfigEntry[InimPrimeRuntimeData]