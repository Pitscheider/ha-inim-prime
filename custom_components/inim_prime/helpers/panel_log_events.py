from datetime import datetime

from gateway import InimPrimeGateway
from models.log_events import UnifiedLogEvent as PanelLogEvent


# ───────────────
# Serialization helpers
# ───────────────
def filter_new_log_events(
        last_log_events: list[PanelLogEvent],
        current_log_events: list[PanelLogEvent]
) -> list[PanelLogEvent]:
    """
    Filters a list of current log events to return only the events that are
    new since the last snapshot of log events.

    Comparison is based on all event attributes except the unique ID.

    Args:
        last_log_events: List of previously seen LogEvent objects.
        current_log_events: List of newly fetched LogEvent objects.

    Returns:
        A list of LogEvent objects from current_log_events that are not
        already included in last_log_events.
    """

    # Helper function to extract a "key" tuple for each log event.
    # This key represents the essential attributes that define equality.
    def event_key(log_event: PanelLogEvent):
        return (
            log_event.timestamp,
            log_event.type,
            log_event.agent,
            log_event.location,
            log_event.value,
        )

    # Convert last and current events to key tuples for easy comparison
    last_keys = [event_key(e) for e in last_log_events]
    current_keys = [event_key(e) for e in current_log_events]

    n_last = len(last_keys)  # number of events in the old list
    n_curr = len(current_keys)  # number of events in the new list

    # -------------------------------
    # Case 0: No old events
    # -------------------------------
    # If the old list is empty, all events are new
    if n_last == 0:
        return current_log_events  # everything in current_log_events is new

    # -------------------------------
    # Case 1: Full overlap at the end
    # -------------------------------
    # Check if the overlapping portion at the end of last_keys
    # matches the end of current_keys. If so, there are no new events.
    # min(n_last, n_curr) ensures we only compare the portion that exists in both lists
    if last_keys[-min(n_last, n_curr):] == current_keys[-min(n_last, n_curr):]:
        return []  # no new events to return

    # -------------------------------
    # Case 2: Old list is shorter than the new list
    # -------------------------------
    # This handles the scenario where last_keys is fully contained in the end of current_keys,
    # and there are new events appended at the end
    if n_last < n_curr:
        for i in range(1, n_curr - n_last + 1):  # check all possible number of new appended events
            if last_keys[:] == current_keys[-(i + n_last):-i]:  # full match of last_keys in current_keys
                return current_log_events[-i:]  # return only the newly appended events

    # -------------------------------
    # Case 3: Partial overlap
    # -------------------------------
    # This handles the situation where the end of last_keys overlaps with the start of current_keys
    # We iterate from the largest possible overlap (but not 1:1 match) down to 1 to find the longest overlap first
    for overlap in range(min(n_last, n_curr) - 1, 0, -1):  # largest → 1
        if last_keys[-overlap:] == current_keys[:overlap]:  # check for suffix-prefix match
            return current_log_events[-(n_curr - overlap):]  # return only events after the overlap

    # -------------------------------
    # Case 4: No overlap at all
    # -------------------------------
    # If none of the above conditions matched, return all current_log_events as new
    return current_log_events


def serialize_panel_log_event(event: PanelLogEvent) -> dict:
    return {
        "id": event.id,
        "timestamp": event.timestamp.isoformat(),
        "type": event.type,
        "agent": event.agent,
        "location": event.location,
        "value": event.value,
    }


def deserialize_panel_log_event(data: dict) -> PanelLogEvent:
    return PanelLogEvent(
        id = data["id"],
        timestamp = datetime.fromisoformat(data["timestamp"]),
        type = data["type"],
        agent = data.get("agent"),
        location = data.get("location"),
        value = data.get("value"),
    )


def serialize_panel_log_events(logs: list[PanelLogEvent]) -> list[dict]:
    return [serialize_panel_log_event(l) for l in logs]


def deserialize_panel_log_events(data: list[dict]) -> list[PanelLogEvent]:
    return [deserialize_panel_log_event(d) for d in data]


async def async_fetch_panel_log_events(
        last_panel_log_events: list[PanelLogEvent],
        gateway: InimPrimeGateway,
        limit: int,
) -> tuple[list[PanelLogEvent] | None, list[PanelLogEvent] | None]:
    try:
        current_panel_log_events = await gateway.get_log_events(limit = limit)
    except Exception as e:
        # Return None in case of issues with the gateway
        return None, None

    # Compare with last saved logs
    current_panel_log_events_filtered = filter_new_log_events(
        last_log_events = last_panel_log_events,
        current_log_events = current_panel_log_events,
    )

    return current_panel_log_events, current_panel_log_events_filtered
