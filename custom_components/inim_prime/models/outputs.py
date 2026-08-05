from dataclasses import dataclass

@dataclass(frozen=True)
class UnifiedOutput:
    output_id: int
    label: str
    state: bool | None

    ### Special methods
    def __hash__(self) -> int:
        return hash(self.output_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UnifiedOutput):
            return NotImplemented

        return self.output_id == other.output_id