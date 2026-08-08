from __future__ import annotations
from types import MappingProxyType
from typing import Any

import voluptuous as vol
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    TextSelector, TextSelectorType, TextSelectorConfig,
    NumberSelector, NumberSelectorConfig, NumberSelectorMode,
)

from .models import FlowData
from ..const import (
    CONF_HOST, CONF_NATIVE, CONF_NATIVE_PASSWORD, CONF_NATIVE_PIN,
    CONF_NATIVE_PORT, CONF_NATIVE_PORT_DEFAULT, CONF_NATIVE_USE_OUTER_FRAME,
    CONF_NATIVE_USE_OUTER_FRAME_DEFAULT, CONF_PRIMELAN, CONF_PRIMELAN_API_KEY,
    CONF_PRIMELAN_USE_HTTPS, CONF_PANEL_LOG_EVENTS_FETCH_LIMIT,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_DEFAULT, CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MIN,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MAX, CONF_SCAN_INTERVAL_MIN, CONF_SCAN_INTERVAL_MAX,
    CONF_ZONES_SCAN_INTERVAL, CONF_PARTITIONS_SCAN_INTERVAL, CONF_GSM_SCAN_INTERVAL,
    CONF_SYSTEM_FAULTS_SCAN_INTERVAL, CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL,
    CONF_ZONES_SCAN_INTERVAL_PRIMELAN_DEFAULT, CONF_PARTITIONS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    CONF_ZONES_SCAN_INTERVAL_NATIVE_DEFAULT, CONF_PARTITIONS_SCAN_INTERVAL_NATIVE_DEFAULT,
    CONF_GSM_SCAN_INTERVAL_PRIMELAN_DEFAULT, CONF_SYSTEM_FAULTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL_PRIMELAN_DEFAULT, CONF_NATIVE_PASSWORD_DEFAULT,
    CONF_PRIMELAN_USE_HTTPS_DEFAULT, CONF_NATIVE_USE_CUSTOM_PIN, CONF_NATIVE_USE_CUSTOM_PIN_DEFAULT,
)

# ... build_native_schema, build_primelan_schema, build_connection_schema,
#     default_scan_intervals, build_options_schema — unchanged bodies, moved here

# ----------------------------------------------------------------------
# Per-backend connection schemas
# ----------------------------------------------------------------------

def build_native_schema(
        *,
        current_host: str | None = None,
        current_port: int | None = None,
        current_use_outer_frame: bool | None = None,
        current_use_custom_pin: bool | None = None,
        require_password: bool = True,
        include_host: bool = True,
) -> dict:
    """Build the native-protocol connection schema.

    include_host=False is used when the host is asked once at the top
    level and shared with the PrimeLAN section (see build_connection_schema).
    """
    schema: dict = {}

    if include_host:
        schema[vol.Required(CONF_HOST, default = current_host)] = str

    schema[vol.Required(
        CONF_NATIVE_PORT,
        default = current_port if current_port is not None else CONF_NATIVE_PORT_DEFAULT,
    )] = int
    schema[vol.Required(
        CONF_NATIVE_USE_OUTER_FRAME,
        default = current_use_outer_frame if current_use_outer_frame is not None else CONF_NATIVE_USE_OUTER_FRAME_DEFAULT,
    )] = bool

    if require_password:
        schema[vol.Required(
            CONF_NATIVE_PASSWORD,
            default = CONF_NATIVE_PASSWORD_DEFAULT,
        )] = TextSelector(TextSelectorConfig(type = TextSelectorType.PASSWORD))
    else:
        schema[vol.Optional(CONF_NATIVE_PASSWORD)] = TextSelector(TextSelectorConfig(type = TextSelectorType.PASSWORD))

    schema[vol.Required(
        CONF_NATIVE_USE_CUSTOM_PIN,
        default = current_use_custom_pin if current_use_custom_pin is not None else CONF_NATIVE_USE_CUSTOM_PIN_DEFAULT,
    )] = bool
    schema[vol.Optional(CONF_NATIVE_PIN)] = TextSelector(TextSelectorConfig(type = TextSelectorType.PASSWORD))

    return schema


def build_primelan_schema(
        *,
        current_host: str | None = None,
        current_use_https: bool | None = None,
        require_api_key: bool = True,
        include_host: bool = True,
) -> dict:
    """Build the PrimeLAN connection schema."""
    schema: dict = {}

    if include_host:
        schema[vol.Required(CONF_HOST, default = current_host)] = str

    schema[vol.Required(
        CONF_PRIMELAN_USE_HTTPS,
        default = current_use_https if current_use_https is not None else CONF_PRIMELAN_USE_HTTPS_DEFAULT,
    )] = bool

    if require_api_key:
        schema[vol.Required(CONF_PRIMELAN_API_KEY)] = TextSelector(
            TextSelectorConfig(type = TextSelectorType.PASSWORD)
        )
    else:
        schema[vol.Optional(CONF_PRIMELAN_API_KEY)] = TextSelector(
            TextSelectorConfig(type = TextSelectorType.PASSWORD)
        )

    return schema


def build_connection_schema(
        *,
        flow_data: FlowData,
) -> dict:
    """Build the combined connection-step schema for the chosen backend(s).

    The host is asked once, at top level, and shared by whichever backend
    section(s) are active -- Native and PrimeLAN always talk to the same
    panel/gateway address.
    """

    schema: dict = {
        vol.Required(CONF_HOST, default = flow_data.host): str,
    }

    if flow_data.use_native:
        if flow_data.native is None:
            schema[vol.Required(CONF_NATIVE)] = section(
                vol.Schema(
                    build_native_schema(
                        require_password = True,
                        include_host = False,
                    )
                )
            )
        else:
            schema[vol.Required(CONF_NATIVE)] = section(
                vol.Schema(
                    build_native_schema(
                        current_port = flow_data.native.port,
                        current_use_outer_frame = flow_data.native.use_outer_frame,
                        current_use_custom_pin = flow_data.native.pin is not None,
                        require_password = False,
                        include_host = False,
                    )
                )
            )

    if flow_data.use_primelan:
        if flow_data.primelan is None:
            schema[vol.Required(CONF_PRIMELAN)] = section(
                vol.Schema(
                    build_primelan_schema(
                        require_api_key = True,
                        include_host = False,
                    )
                )
            )
        else:
            schema[vol.Required(CONF_PRIMELAN)] = section(
                vol.Schema(
                    build_primelan_schema(
                        current_use_https = flow_data.primelan.use_https,
                        require_api_key = False,
                        include_host = False,
                    )
                )
            )

    return schema


# ----------------------------------------------------------------------
# Integration options schema (scan intervals, log fetch limit)
# ----------------------------------------------------------------------

def default_scan_intervals(*, has_native: bool) -> dict:
    """Zones/partitions defaults, tightened when Native (local) is active."""
    return {
        CONF_ZONES_SCAN_INTERVAL: (
            CONF_ZONES_SCAN_INTERVAL_NATIVE_DEFAULT if has_native else CONF_ZONES_SCAN_INTERVAL_PRIMELAN_DEFAULT
        ),
        CONF_PARTITIONS_SCAN_INTERVAL: (
            CONF_PARTITIONS_SCAN_INTERVAL_NATIVE_DEFAULT if has_native else CONF_PARTITIONS_SCAN_INTERVAL_PRIMELAN_DEFAULT
        ),
    }


def build_options_schema(
        *,
        has_native: bool,
        has_primelan: bool,
        defaults: MappingProxyType[str, Any] | None = None,
) -> dict:
    """Build the options schema, only including fields the active backend(s) support.

    GSM / system faults / log events (and their fetch limit) are
    PrimeLAN-exclusive today, so they're omitted entirely when PrimeLAN
    isn't configured for this entry.
    """
    defaults = defaults or {}
    scan_defaults = default_scan_intervals(has_native = has_native)

    scan_interval_fields: dict = {
        vol.Required(
            CONF_ZONES_SCAN_INTERVAL,
            default = defaults.get(CONF_ZONES_SCAN_INTERVAL, scan_defaults[CONF_ZONES_SCAN_INTERVAL]),
        ): NumberSelector(NumberSelectorConfig(
            min = CONF_SCAN_INTERVAL_MIN,
            max = CONF_SCAN_INTERVAL_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        )),
        vol.Required(
            CONF_PARTITIONS_SCAN_INTERVAL,
            default = defaults.get(CONF_PARTITIONS_SCAN_INTERVAL, scan_defaults[CONF_PARTITIONS_SCAN_INTERVAL]),
        ): NumberSelector(NumberSelectorConfig(
            min = CONF_SCAN_INTERVAL_MIN,
            max = CONF_SCAN_INTERVAL_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        )),
    }

    if has_primelan:
        scan_interval_fields[vol.Required(
            CONF_GSM_SCAN_INTERVAL,
            default = defaults.get(CONF_GSM_SCAN_INTERVAL, CONF_GSM_SCAN_INTERVAL_PRIMELAN_DEFAULT),
        )] = NumberSelector(NumberSelectorConfig(
            min = CONF_SCAN_INTERVAL_MIN,
            max = CONF_SCAN_INTERVAL_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        ))

        scan_interval_fields[vol.Required(
            CONF_SYSTEM_FAULTS_SCAN_INTERVAL,
            default = defaults.get(CONF_SYSTEM_FAULTS_SCAN_INTERVAL, CONF_SYSTEM_FAULTS_SCAN_INTERVAL_PRIMELAN_DEFAULT),
        )] = NumberSelector(NumberSelectorConfig(
            min = CONF_SCAN_INTERVAL_MIN,
            max = CONF_SCAN_INTERVAL_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        ))

        scan_interval_fields[vol.Required(
            CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL,
            default = defaults.get(
                CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL, CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL_PRIMELAN_DEFAULT
            ),
        )] = NumberSelector(NumberSelectorConfig(
            min = CONF_SCAN_INTERVAL_MIN,
            max = CONF_SCAN_INTERVAL_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        ))

    schema: dict = {
        vol.Required("scan_intervals"): section(vol.Schema(scan_interval_fields)),
    }

    if has_primelan:
        schema[vol.Required(
            CONF_PANEL_LOG_EVENTS_FETCH_LIMIT,
            default = defaults.get(CONF_PANEL_LOG_EVENTS_FETCH_LIMIT, CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_DEFAULT),
        )] = NumberSelector(NumberSelectorConfig(
            min = CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MIN,
            max = CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        ))
    return schema