DOMAIN = "inim_prime"

CONF_HOST = "host"
CONF_PRIMELAN_API_KEY = "api_key"
CONF_PRIMELAN_USE_HTTPS = "use_https"
CONF_SERIAL_NUMBER = "serial_number"
CONF_PANEL_LOG_EVENTS_FETCH_LIMIT = "panel_log_events_fetch_limit"
CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_DEFAULT = 40
CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_TRIGGER = 3
CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MIN = 10
CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MAX = 100

# --- Backend section keys (top-level in entry.data) ---
# entry.data holds: {serial_number, native?: {...}, primelan?: {...}}
# At least one of "native" / "primelan" must be present. Presence is what
# gates a backend on/off -- there is no separate enabled flag.
CONF_NATIVE = "native"
CONF_PRIMELAN = "primelan"

# --- Native connection fields (nested under entry.data["native"]) ---
CONF_NATIVE_PORT = "port"
CONF_NATIVE_PASSWORD = "password"
CONF_NATIVE_PIN = "pin"
CONF_NATIVE_USE_OUTER_FRAME = "use_outer_frame"

CONF_NATIVE_PORT_DEFAULT = 6004  # inim.prime.native.const.Panel.DEFAULT_PORT
CONF_NATIVE_USE_OUTER_FRAME_DEFAULT = True  # True when connecting via the PrimeLAN card


# Coordinators
ZONES_COORDINATOR = "zones_coordinator"
PARTITIONS_COORDINATOR = "partitions_coordinator"
GSM_COORDINATOR = "gsm_coordinator"
SYSTEM_FAULTS_COORDINATOR = "system_faults_coordinator"
PANEL_LOG_EVENTS_COORDINATOR = "panel_log_events_coordinator"

# --- Scan interval config keys ---
CONF_ZONES_SCAN_INTERVAL = "zones_scan_interval"
CONF_PARTITIONS_SCAN_INTERVAL = "partitions_scan_interval"
CONF_GSM_SCAN_INTERVAL = "gsm_scan_interval"
CONF_SYSTEM_FAULTS_SCAN_INTERVAL = "system_faults_scan_interval"
CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL = "panel_log_events_scan_interval"

# --- Defaults (custom per coordinator) ---
CONF_ZONES_SCAN_INTERVAL_DEFAULT = 5
CONF_PARTITIONS_SCAN_INTERVAL_DEFAULT = 10
CONF_GSM_SCAN_INTERVAL_DEFAULT = 30
CONF_SYSTEM_FAULTS_SCAN_INTERVAL_DEFAULT = 15
CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL_DEFAULT = 15

CONF_SCAN_INTERVAL_MIN = 1
CONF_SCAN_INTERVAL_MAX = 300

STORAGE_KEY_LAST_PANEL_EVENT_LOGS = "last_panel_event_logs"

INIM_PRIME_DEVICE_MANUFACTURER = "Inim"
INIM_PRIME_MODEL_ZONE = "Prime Zone"
