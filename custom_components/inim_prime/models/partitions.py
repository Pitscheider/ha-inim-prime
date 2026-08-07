from dataclasses import dataclass
from enum import Enum, auto


class UnifiedPartitionState(Enum):
    OK = auto()
    ALARM = auto()
    TAMPER = auto()

class UnifiedArmingStatus(Enum):
    ARM_AWAY = auto()
    ARM_STAY = auto()
    ARM_INSTANT = auto()
    DISARMED = auto()

@dataclass(frozen=True)
class UnifiedPartition:
    ### Attributes
    partition_id: int
    label: str
    zones: set[int] | None
    arming_status: UnifiedArmingStatus | None
    partition_state: UnifiedPartitionState | None
    alarm_memory: bool | None

    ### Special methods
    def __hash__(self) -> int:
        return hash(self.partition_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UnifiedPartition):
            return NotImplemented

        return self.partition_id == other.partition_id