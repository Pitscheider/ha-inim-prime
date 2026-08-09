from __future__ import annotations
from dataclasses import dataclass
from typing import TypedDict

from ..custom_types import InimPrimeConfigData, NativeConfigData, PrimelanConfigData, InimPrimeOptionsData, \
    ScanIntervalsData


@dataclass
class NativeConfig:
    port: int
    password: str
    use_outer_frame: bool
    pin: str | None

    def to_dict(self) -> NativeConfigData:
        return {
            "port": self.port,
            "password": self.password,
            "use_outer_frame": self.use_outer_frame,
            "pin": self.pin,
        }


@dataclass
class PrimelanConfig:
    api_key: str
    use_https: bool

    def to_dict(self) -> PrimelanConfigData:
        return {"api_key": self.api_key, "use_https": self.use_https}


@dataclass
class FlowData:
    serial_number: str | None = None
    host: str | None = None
    use_native: bool = False
    use_primelan: bool = False
    native: NativeConfig | None = None
    primelan: PrimelanConfig | None = None

    def to_entry_data(self) -> InimPrimeConfigData:
        assert self.serial_number is not None
        assert self.host is not None
        data: InimPrimeConfigData = {
            "serial_number": self.serial_number,
            "host": self.host,
        }
        if self.native is not None:
            data["native"] = self.native.to_dict()
        if self.primelan is not None:
            data["primelan"] = self.primelan.to_dict()
        return data


@dataclass
class OptionsData:
    zones_scan_interval: int | None = None
    partitions_scan_interval: int | None = None
    gsm_scan_interval: int | None = None
    system_faults_scan_interval: int | None = None
    panel_log_events_scan_interval: int | None = None
    panel_log_events_fetch_limit: int | None = None

    def to_options_dict(self) -> InimPrimeOptionsData:
        assert self.zones_scan_interval is not None
        assert self.partitions_scan_interval is not None

        scan_intervals: ScanIntervalsData = {
            "zones": self.zones_scan_interval,
            "partitions": self.partitions_scan_interval,
        }
        if self.gsm_scan_interval is not None:
            scan_intervals["gsm"] = self.gsm_scan_interval
        if self.system_faults_scan_interval is not None:
            scan_intervals["system_faults"] = self.system_faults_scan_interval
        if self.panel_log_events_scan_interval is not None:
            scan_intervals["panel_log_events"] = self.panel_log_events_scan_interval

        options: InimPrimeOptionsData = {"scan_intervals": scan_intervals}
        if self.panel_log_events_fetch_limit is not None:
            options["panel_log_events_fetch_limit"] = self.panel_log_events_fetch_limit
        return options

class ScanIntervalsDefault(TypedDict):
    zones: int
    partitions: int
    gsm: int
    system_faults: int
    panel_log_events: int