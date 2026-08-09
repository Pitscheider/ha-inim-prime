from __future__ import annotations

import voluptuous as vol
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    TextSelector, TextSelectorType, TextSelectorConfig,
    NumberSelector, NumberSelectorConfig, NumberSelectorMode,
)

from .const import (
    DataKey,
    OptionsKey,
)
from .models import ConfigData, ScanIntervalsDefault, ConfigOptions
from ..const import (
    ZONES_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    PARTITIONS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    ZONES_SCAN_INTERVAL_NATIVE_DEFAULT,
    PARTITIONS_SCAN_INTERVAL_NATIVE_DEFAULT,
    GSM_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    SYSTEM_FAULTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    PANEL_LOG_EVENTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    NATIVE_PASSWORD_DEFAULT,
    PRIMELAN_USE_HTTPS_DEFAULT,
    NATIVE_USE_CUSTOM_PIN_DEFAULT,
    NATIVE_PORT_DEFAULT,
    NATIVE_USE_OUTER_FRAME_DEFAULT,
    SCAN_INTERVAL_MIN,
    SCAN_INTERVAL_MAX,
    PANEL_LOG_EVENTS_FETCH_LIMIT_DEFAULT,
    PANEL_LOG_EVENTS_FETCH_LIMIT_MIN,
    PANEL_LOG_EVENTS_FETCH_LIMIT_MAX,
)


# ----------------------------------------------------------------------
# Per-backend connection schemas
# ----------------------------------------------------------------------

def build_native_schema(
        *,
        current_port: int | None = None,
        current_use_outer_frame: bool | None = None,
        current_use_custom_pin: bool | None = None,
        require_password: bool = True,
) -> dict:
    """Build the native-protocol connection schema.

    include_host=False is used when the host is asked once at the top
    level and shared with the PrimeLAN section (see build_connection_schema).
    """
    schema: dict = {}

    # Port
    schema[vol.Required(
        DataKey.Native.PORT,
        default = current_port if current_port is not None else NATIVE_PORT_DEFAULT,
    )] = int

    # Use outer frame
    schema[vol.Required(
        DataKey.Native.USE_OUTER_FRAME,
        default = current_use_outer_frame if current_use_outer_frame is not None else NATIVE_USE_OUTER_FRAME_DEFAULT,
    )] = bool

    # Password
    if require_password:
        schema[vol.Required(
            DataKey.Native.PASSWORD,
            default = NATIVE_PASSWORD_DEFAULT,
        )] = TextSelector(TextSelectorConfig(type = TextSelectorType.PASSWORD))
    else:
        schema[vol.Optional(
            DataKey.Native.PASSWORD,
        )] = TextSelector(TextSelectorConfig(type = TextSelectorType.PASSWORD))

    # Use custom pin
    schema[vol.Required(
        DataKey.Native.USE_CUSTOM_PIN,
        default = current_use_custom_pin if current_use_custom_pin is not None else NATIVE_USE_CUSTOM_PIN_DEFAULT,
    )] = bool

    # Pin
    schema[vol.Optional(
        DataKey.Native.PIN,
    )] = TextSelector(TextSelectorConfig(type = TextSelectorType.PASSWORD))

    return schema


def build_primelan_schema(
        *,
        current_use_https: bool | None = None,
        require_api_key: bool = True,
) -> dict:
    """Build the PrimeLAN connection schema."""
    schema: dict = {}


    # Use https
    schema[vol.Required(
        DataKey.Primelan.USE_HTTPS,
        default = current_use_https if current_use_https is not None else PRIMELAN_USE_HTTPS_DEFAULT,
    )] = bool

    # Api key
    if require_api_key:
        schema[vol.Required(DataKey.Primelan.API_KEY)] = TextSelector(
            TextSelectorConfig(type = TextSelectorType.PASSWORD)
        )
    else:
        schema[vol.Optional(DataKey.Primelan.API_KEY)] = TextSelector(
            TextSelectorConfig(type = TextSelectorType.PASSWORD)
        )

    return schema


def build_connection_schema(
        *,
        flow_data: ConfigData,
) -> dict:
    """Build the combined connection-step schema for the chosen backend(s).

    The host is asked once, at top level, and shared by whichever backend
    section(s) are active -- Native and PrimeLAN always talk to the same
    panel/gateway address.
    """

    schema: dict = {
        vol.Required(DataKey.HOST, default = flow_data.host): str,
    }

    if flow_data.use_native:
        if flow_data.native is None:
            schema[vol.Required(DataKey.NATIVE)] = section(
                vol.Schema(
                    build_native_schema(
                        require_password = True,
                    )
                )
            )
        else:
            schema[vol.Required(DataKey.NATIVE)] = section(
                vol.Schema(
                    build_native_schema(
                        current_port = flow_data.native.port,
                        current_use_outer_frame = flow_data.native.use_outer_frame,
                        current_use_custom_pin = flow_data.native.pin is not None,
                        require_password = False,
                    )
                )
            )

    if flow_data.use_primelan:
        if flow_data.primelan is None:
            schema[vol.Required(DataKey.PRIMELAN)] = section(
                vol.Schema(
                    build_primelan_schema(
                        require_api_key = True,
                    )
                )
            )
        else:
            schema[vol.Required(DataKey.PRIMELAN)] = section(
                vol.Schema(
                    build_primelan_schema(
                        current_use_https = flow_data.primelan.use_https,
                        require_api_key = False,
                    )
                )
            )

    return schema


# ----------------------------------------------------------------------
# Integration options schema (scan intervals, log fetch limit)
# ----------------------------------------------------------------------

def build_options_schema(
        *,
        has_native: bool,
        has_primelan: bool,
        current_options: ConfigOptions | None = None,
        migrating_from_native: bool | None = None,
        migrating_from_primelan: bool | None = None,
) -> dict:
    """Build the options schema, only including fields the active backend(s) support.

    GSM / system faults / log events (and their fetch limit) are
    PrimeLAN-exclusive today, so they're omitted entirely when PrimeLAN
    isn't configured for this entry.
    """
    panel_log_events_fetch_limit = PANEL_LOG_EVENTS_FETCH_LIMIT_DEFAULT
    scan_intervals_defaults = ScanIntervalsDefault(
        zones = ZONES_SCAN_INTERVAL_NATIVE_DEFAULT if has_native else ZONES_SCAN_INTERVAL_PRIMELAN_DEFAULT,
        partitions = PARTITIONS_SCAN_INTERVAL_NATIVE_DEFAULT if has_native else PARTITIONS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
        gsm = GSM_SCAN_INTERVAL_PRIMELAN_DEFAULT,
        system_faults = SYSTEM_FAULTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
        panel_log_events = PANEL_LOG_EVENTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    )

    if current_options is not None:
        # In case the user is migrating from native or primelan does not use the existing intervals for zones and partitions
        # This is to help the user who does not know that a different backend has different timings
        if (migrating_from_native and has_primelan and not has_native) or (migrating_from_primelan and has_native):
            scan_intervals_defaults["zones"] = current_options.zones_scan_interval if current_options.zones_scan_interval is not None else scan_intervals_defaults["zones"]
            scan_intervals_defaults["partitions"] = current_options.partitions_scan_interval if current_options.partitions_scan_interval is not None else scan_intervals_defaults["partitions"]
        scan_intervals_defaults["gsm"] = current_options.gsm_scan_interval if current_options.gsm_scan_interval is not None else scan_intervals_defaults["gsm"]
        scan_intervals_defaults["system_faults"] = current_options.system_faults_scan_interval if current_options.system_faults_scan_interval is not None else scan_intervals_defaults["system_faults"]
        scan_intervals_defaults["panel_log_events"] = current_options.panel_log_events_scan_interval if current_options.panel_log_events_scan_interval is not None else scan_intervals_defaults["panel_log_events"]

        panel_log_events_fetch_limit = current_options.panel_log_events_fetch_limit if current_options.panel_log_events_fetch_limit is not None else panel_log_events_fetch_limit

    scan_interval_fields: dict = {
        vol.Required(
            OptionsKey.ScanIntervals.ZONES,
            default = scan_intervals_defaults["zones"],
        ): NumberSelector(NumberSelectorConfig(
            min = SCAN_INTERVAL_MIN,
            max = SCAN_INTERVAL_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        )),
        vol.Required(
            OptionsKey.ScanIntervals.PARTITIONS,
            default = scan_intervals_defaults["partitions"],
        ): NumberSelector(NumberSelectorConfig(
            min = SCAN_INTERVAL_MIN,
            max = SCAN_INTERVAL_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        )),
    }

    if has_primelan:
        scan_interval_fields[vol.Required(
            OptionsKey.ScanIntervals.GSM,
            default = scan_intervals_defaults["gsm"],
        )] = NumberSelector(NumberSelectorConfig(
            min = SCAN_INTERVAL_MIN,
            max = SCAN_INTERVAL_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        ))

        scan_interval_fields[vol.Required(
            OptionsKey.ScanIntervals.SYSTEM_FAULTS,
            default = scan_intervals_defaults["system_faults"],
        )] = NumberSelector(NumberSelectorConfig(
            min = SCAN_INTERVAL_MIN,
            max = SCAN_INTERVAL_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        ))

        scan_interval_fields[vol.Required(
            OptionsKey.ScanIntervals.PANEL_LOG_EVENTS,
            default = scan_intervals_defaults["panel_log_events"],
        )] = NumberSelector(NumberSelectorConfig(
            min = SCAN_INTERVAL_MIN,
            max = SCAN_INTERVAL_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        ))

    schema: dict = {
        vol.Required("scan_intervals"): section(vol.Schema(scan_interval_fields)),
    }

    if has_primelan:
        schema[vol.Required(
            OptionsKey.PANEL_LOG_EVENTS_FETCH_LIMIT,
            default = panel_log_events_fetch_limit,
        )] = NumberSelector(NumberSelectorConfig(
            min = PANEL_LOG_EVENTS_FETCH_LIMIT_MIN,
            max = PANEL_LOG_EVENTS_FETCH_LIMIT_MAX,
            mode = NumberSelectorMode.BOX,
        ))
    return schema