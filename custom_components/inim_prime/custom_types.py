from dataclasses import dataclass
from typing import TypedDict, NotRequired, cast

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


class NativeConfigData(TypedDict):
    port: int
    password: str
    use_outer_frame: bool
    pin: str | None


class PrimelanConfigData(TypedDict):
    api_key: str
    use_https: bool


class InimPrimeConfigData(TypedDict):
    """Shape of entry.data as actually stored on disk."""
    serial_number: str
    host: str
    native: NotRequired[NativeConfigData]
    primelan: NotRequired[PrimelanConfigData]


class ScanIntervalsData(TypedDict):
    zones: int
    partitions: int
    gsm: NotRequired[int]
    system_faults: NotRequired[int]
    panel_log_events: NotRequired[int]


class InimPrimeOptionsData(TypedDict):
    scan_intervals: ScanIntervalsData
    panel_log_events_fetch_limit: NotRequired[int]

def get_entry_data(entry: ConfigEntry) -> InimPrimeConfigData:
    return cast(InimPrimeConfigData, cast(object, entry.data))

def get_entry_options(entry: ConfigEntry) -> InimPrimeOptionsData:
    return cast(InimPrimeOptionsData, cast(object, entry.options))