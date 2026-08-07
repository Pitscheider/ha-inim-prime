from dataclasses import dataclass
from enum import Enum, auto


class UnifiedZoneState(Enum):
    TAMPER = auto
    STANDBY = auto
    ALARM = auto
    SHORT_CIRCUIT = auto
    UNKNOWN = auto


@dataclass(frozen = True)
class UnifiedZone:
    zone_id: int
    label: str
    partitions: frozenset[int] | None
    state: UnifiedZoneState | None
    bypass: bool | None
    alarm_memory: bool | None

    ### Special methods
    def __hash__(self) -> int:
        return hash(self.zone_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UnifiedZone):
            return NotImplemented

        return self.zone_id == other.zone_id
