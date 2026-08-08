from typing import Final

import inim.prime.native.const

DOMAIN: Final[str] = "inim_prime"


CONF_PANEL_LOG_EVENTS_FETCH_LIMIT: Final[str] = "panel_log_events_fetch_limit"
CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_DEFAULT: Final[int] = 40
CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_TRIGGER: Final[int] = 3
CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MIN: Final[int] = 10
CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MAX: Final[int] = 100

# --- Backend section keys (top-level in entry.data) ---
# entry.data holds: {serial_number, native?: {...}, primelan?: {...}}
# At least one of "native" / "primelan" must be present. Presence is what
# gates a backend on/off -- there is no separate enabled flag.
CONF_NATIVE: Final[str] = "native"
CONF_PRIMELAN: Final[str] = "primelan"

# General connection fields
CONF_HOST: Final[str] = "host"
CONF_SERIAL_NUMBER: Final[str] = "serial_number"

# Native connection fields
CONF_NATIVE_PORT: Final[str] = "port"
CONF_NATIVE_USE_OUTER_FRAME: Final[str] = "use_outer_frame"
CONF_NATIVE_PASSWORD: Final[str] = "password"
CONF_NATIVE_USE_CUSTOM_PIN: Final[str] = "use_custom_pin"
CONF_NATIVE_PIN: Final[str] = "pin"

CONF_NATIVE_PORT_DEFAULT: Final[int] = inim.prime.native.const.Panel.DEFAULT_PORT
CONF_NATIVE_USE_OUTER_FRAME_DEFAULT: Final[bool] = False
CONF_NATIVE_PASSWORD_DEFAULT: Final[str] = inim.prime.native.const.Panel.DEFAULT_PASSWORD
CONF_NATIVE_USE_CUSTOM_PIN_DEFAULT: Final[bool] = False
CONF_NATIVE_PIN_MAX_CHARACTERS: Final[int] = inim.prime.native.const.Panel.MAX_PIN_CHARACTERS

# Primelan connection fields
CONF_PRIMELAN_API_KEY: Final[str] = "api_key"
CONF_PRIMELAN_USE_HTTPS: Final[str] = "use_https"

CONF_PRIMELAN_USE_HTTPS_DEFAULT: Final[bool] = True

# Coordinators
ZONES_COORDINATOR: Final[str] = "zones_coordinator"
PARTITIONS_COORDINATOR: Final[str] = "partitions_coordinator"
GSM_COORDINATOR: Final[str] = "gsm_coordinator"
SYSTEM_FAULTS_COORDINATOR: Final[str] = "system_faults_coordinator"
PANEL_LOG_EVENTS_COORDINATOR: Final[str] = "panel_log_events_coordinator"

# --- Scan interval config keys ---
CONF_ZONES_SCAN_INTERVAL: Final[str] = "zones"
CONF_PARTITIONS_SCAN_INTERVAL: Final[str] = "partitions"
CONF_GSM_SCAN_INTERVAL: Final[str] = "gsm"
CONF_SYSTEM_FAULTS_SCAN_INTERVAL: Final[str] = "system_faults"
CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL: Final[str] = "panel_log_events"

# --- Defaults (custom per coordinator) ---
CONF_ZONES_SCAN_INTERVAL_NATIVE_DEFAULT: Final[int] = 500
CONF_PARTITIONS_SCAN_INTERVAL_NATIVE_DEFAULT: Final[int] = 500

CONF_ZONES_SCAN_INTERVAL_PRIMELAN_DEFAULT: Final[int] = 5000
CONF_PARTITIONS_SCAN_INTERVAL_PRIMELAN_DEFAULT: Final[int] = 10000
CONF_GSM_SCAN_INTERVAL_PRIMELAN_DEFAULT: Final[int] = 30000
CONF_SYSTEM_FAULTS_SCAN_INTERVAL_PRIMELAN_DEFAULT: Final[int] = 15000
CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL_PRIMELAN_DEFAULT: Final[int] = 15000

CONF_SCAN_INTERVAL_MIN: Final[int] = 1
CONF_SCAN_INTERVAL_MAX: Final[int] = 300000

STORAGE_KEY_LAST_PANEL_EVENT_LOGS = "last_panel_event_logs"

INIM_PRIME_DEVICE_MANUFACTURER = "Inim"
INIM_PRIME_MODEL_ZONE = "Prime Zone"
