from dataclasses import dataclass


@dataclass(frozen = True)
class UnifiedGSM:
    supply_voltage: float | None
    firmware_version: str | None
    operator: str | None
    signal_strength: int | None
    credit: str | None