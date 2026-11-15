from collections.abc import Mapping
from dataclasses import dataclass

from .partitions import UnifiedArmingStatus


@dataclass(frozen = True)
class UnifiedArmingScenario:
    arming_scenario_id: int
    label: str
    # Partitions the scenario changes, mapped to their target arming status.
    # Partitions left unchanged ("-") are not included.
    targets: Mapping[int, UnifiedArmingStatus]

    ### Special methods
    def __hash__(self) -> int:
        return hash(self.arming_scenario_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UnifiedArmingScenario):
            return NotImplemented

        return self.arming_scenario_id == other.arming_scenario_id