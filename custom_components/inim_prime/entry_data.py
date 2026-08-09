"""Typed shapes for entry.data / entry.options as persisted to disk.

Pure data description -- no dependency on coordinators, gateway, or
anything else in this integration, so it's safe to import from any
module without risk of a circular import.
"""
from __future__ import annotations

from typing import TypedDict, NotRequired, cast

from homeassistant.config_entries import ConfigEntry


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