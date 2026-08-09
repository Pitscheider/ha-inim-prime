from typing import Final


class DataKey:
    SERIAL_NUMBER: Final = "serial_number"
    HOST: Final = "host"
    NATIVE: Final = "native"
    PRIMELAN: Final = "primelan"

    class Native:
        PORT: Final = "port"
        USE_OUTER_FRAME: Final = "use_outer_frame"
        PASSWORD: Final = "password"
        USE_CUSTOM_PIN: Final = "use_custom_pin"
        PIN: Final = "pin"

    class Primelan:
        API_KEY: Final = "api_key"
        USE_HTTPS: Final = "use_https"

class OptionsKey:
    PANEL_LOG_EVENTS_FETCH_LIMIT: Final = "panel_log_events_fetch_limit"
    SCAN_INTERVALS: Final = "scan_intervals"

    class ScanIntervals:
        ZONES: Final[str] = "zones"
        PARTITIONS: Final[str] = "partitions"
        GSM: Final[str] = "gsm"
        SYSTEM_FAULTS: Final[str] = "system_faults"
        PANEL_LOG_EVENTS: Final[str] = "panel_log_events"


