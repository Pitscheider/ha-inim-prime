from datetime import datetime
from typing import List, Optional

from inim.prime.primelan.client import InimPrimeClient
from inim.prime.primelan.helpers.log_events import filter_new_log_events
from inim.prime.primelan.models.log_event import LogEvent


# ───────────────
# Serialization helpers
# ───────────────
def serialize_panel_log_event(event: LogEvent) -> dict:
    return {
        "id": event.id,
        "timestamp": event.timestamp.isoformat(),
        "type": event.type,
        "agent": event.agent,
        "location": event.location,
        "value": event.value,
    }


def deserialize_panel_log_event(data: dict) -> LogEvent:
    return LogEvent(
        id = data["id"],
        timestamp = datetime.fromisoformat(data["timestamp"]),
        type = data["type"],
        agent = data.get("agent"),
        location = data.get("location"),
        value = data.get("value"),
    )


def serialize_panel_log_events(logs: List[LogEvent]) -> list[dict]:
    return [serialize_panel_log_event(l) for l in logs]


def deserialize_panel_log_events(data: list[dict]) -> List[LogEvent]:
    return [deserialize_panel_log_event(d) for d in data]


async def async_fetch_panel_log_events(
        last_panel_log_events: List[LogEvent],
        client: InimPrimeClient,
        limit: int,
) -> tuple[Optional[List[LogEvent]], Optional[List[LogEvent]]]:
    try:
        current_panel_log_events = await client.get_log_events(limit = limit)
    except Exception as e:
        # Return None in case of issues with the client
        return None, None

    # Compare with last saved logs
    current_panel_log_events_filtered = filter_new_log_events(
        last_log_events = last_panel_log_events,
        current_log_events = current_panel_log_events,
    )

    return current_panel_log_events, current_panel_log_events_filtered
