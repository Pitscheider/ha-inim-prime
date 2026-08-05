from dataclasses import dataclass
from enum import Enum, auto
from typing import FrozenSet

class UnifiedSystemFault(Enum):
    RESERVED_0 = auto
    RESERVED_1 = auto
    LOW_BATTERY = auto
    NETWORK_FAULT = auto
    NO_TELEPHONE_LINE = auto
    RADIO_JAMMING = auto
    LOW_BATTERY_WIRELESS = auto
    WIRELESS_DEVICE_DISAPPEARANCE = auto
    GSM_FAULT = auto
    SENSOR_DIRTY = auto
    ZONE_FAULT = auto
    SIRENS_FAULT = auto
    POWER_SUPPLY_FAULT = auto
    RADIO_KEYBOARDS_FAULT = auto
    SABOTAGE_FAULT = auto
    INTERNET_FAULT = auto

UNIFIED_EXPOSED_SYSTEM_FAULTS: FrozenSet[UnifiedSystemFault] = frozenset({
    UnifiedSystemFault.LOW_BATTERY,
    UnifiedSystemFault.NETWORK_FAULT,
    UnifiedSystemFault.NO_TELEPHONE_LINE,
    UnifiedSystemFault.RADIO_JAMMING,
    UnifiedSystemFault.LOW_BATTERY_WIRELESS,
    UnifiedSystemFault.WIRELESS_DEVICE_DISAPPEARANCE,
    UnifiedSystemFault.GSM_FAULT,
    UnifiedSystemFault.SENSOR_DIRTY,
    UnifiedSystemFault.ZONE_FAULT,
    UnifiedSystemFault.SIRENS_FAULT,
    UnifiedSystemFault.POWER_SUPPLY_FAULT,
    UnifiedSystemFault.RADIO_KEYBOARDS_FAULT,
    UnifiedSystemFault.SABOTAGE_FAULT,
    UnifiedSystemFault.INTERNET_FAULT,
})

@dataclass(frozen = True)
class UnifiedSystemFaults:
    supply_voltage: float | None

    faults: FrozenSet[UnifiedSystemFault]

    def has_fault(self, fault) -> bool:
        return fault in self.faults

    @property
    def has_any_fault(self) -> bool:
        return bool(self.faults)

    @property
    def fault_count(self) -> int:
        return len(self.faults)