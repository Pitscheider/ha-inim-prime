from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen = True)
class UnifiedLogEvent:
    id: int
    timestamp: datetime
    type: str
    agent: str | None
    location: str | None
    value: str | None
