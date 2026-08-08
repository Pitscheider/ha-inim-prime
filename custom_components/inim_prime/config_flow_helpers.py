"""Schema builders and connection testers for the INIM Prime config flow.

Kept separate from config_flow.py so the flow-step logic (navigation,
state accumulation) stays readable and the "how do I build this form" /
"how do I test this backend" concerns are modular and independently
testable.
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Any

import voluptuous as vol
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import TextSelector, TextSelectorType, TextSelectorConfig, NumberSelector, \
    NumberSelectorConfig, NumberSelectorMode

from inim.prime.native.client import Client as NativeClient
from inim.prime.primelan.client import InimPrimeClient

from .const import (
    CONF_HOST,
    CONF_NATIVE,
    CONF_NATIVE_PASSWORD,
    CONF_NATIVE_PIN,
    CONF_NATIVE_PORT,
    CONF_NATIVE_PORT_DEFAULT,
    CONF_NATIVE_USE_OUTER_FRAME,
    CONF_NATIVE_USE_OUTER_FRAME_DEFAULT,
    CONF_PRIMELAN,
    CONF_PRIMELAN_API_KEY,
    CONF_PRIMELAN_USE_HTTPS,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_DEFAULT,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MIN,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MAX,
    CONF_SCAN_INTERVAL_MIN,
    CONF_SCAN_INTERVAL_MAX,
    CONF_ZONES_SCAN_INTERVAL,
    CONF_PARTITIONS_SCAN_INTERVAL,
    CONF_GSM_SCAN_INTERVAL,
    CONF_SYSTEM_FAULTS_SCAN_INTERVAL,
    CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL,
    CONF_ZONES_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    CONF_PARTITIONS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    CONF_ZONES_SCAN_INTERVAL_NATIVE_DEFAULT,
    CONF_PARTITIONS_SCAN_INTERVAL_NATIVE_DEFAULT,
    CONF_GSM_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    CONF_SYSTEM_FAULTS_SCAN_INTERVAL_PRIMELAN_DEFAULT,
    CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL_PRIMELAN_DEFAULT, CONF_NATIVE_PASSWORD_DEFAULT, CONF_PRIMELAN_USE_HTTPS_DEFAULT,
    CONF_NATIVE_USE_CUSTOM_PIN, CONF_NATIVE_USE_CUSTOM_PIN_DEFAULT,
)


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
        backends: set[str],
        default_host: str | None = None,
        native_defaults: dict | None = None,
        primelan_defaults: dict | None = None,
) -> dict:
    """Build the combined connection-step schema for the chosen backend(s).

    The host is asked once, at top level, and shared by whichever backend
    section(s) are active -- Native and PrimeLAN always talk to the same
    panel/gateway address.
    """

    schema: dict = {
        vol.Required(CONF_HOST, default = default_host): str,
    }

    if CONF_NATIVE in backends:
        if native_defaults is None:
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
                        current_port = native_defaults.get(CONF_NATIVE_PORT),
                        current_use_outer_frame = native_defaults.get(CONF_NATIVE_USE_OUTER_FRAME),
                        current_use_custom_pin = native_defaults.get(CONF_NATIVE_USE_CUSTOM_PIN),
                        require_password = False,
                        include_host = False,
                    )
                )
            )

    if CONF_PRIMELAN in backends:
        if primelan_defaults is None:
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
                        current_use_https = primelan_defaults.get(CONF_PRIMELAN_USE_HTTPS, True),
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
        )),
        scan_interval_fields[vol.Required(
            CONF_SYSTEM_FAULTS_SCAN_INTERVAL,
            default = defaults.get(CONF_SYSTEM_FAULTS_SCAN_INTERVAL, CONF_SYSTEM_FAULTS_SCAN_INTERVAL_PRIMELAN_DEFAULT),
        )] = NumberSelector(NumberSelectorConfig(
            min = CONF_SCAN_INTERVAL_MIN,
            max = CONF_SCAN_INTERVAL_MAX,
            mode = NumberSelectorMode.BOX,
            unit_of_measurement = "milliseconds",
        )),
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
        )),

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
        )),
    return schema


# ----------------------------------------------------------------------
# Connection testing
# ----------------------------------------------------------------------

async def test_native_connection(conf: dict) -> None:
    """Test a native connection without keeping it open (used by reconfigure)."""
    client = NativeClient(
        host = conf[CONF_HOST].strip(),
        password = conf[CONF_NATIVE_PASSWORD].strip(),
        use_outer_frame = conf[CONF_NATIVE_USE_OUTER_FRAME],
        port = conf[CONF_NATIVE_PORT],
        pin = conf[CONF_NATIVE_PIN].strip() if conf[CONF_NATIVE_USE_CUSTOM_PIN] else None,
    )
    await client.connect()
    await client.initialize()
    client.disconnect()


async def test_native_connection_and_get_serial(conf: dict) -> str:
    """Test a native connection and return the panel serial number.

    Used during initial setup when Native is active: the serial number
    (needed as the entry's unique_id) is retrieved automatically instead
    of being asked to the user.
    """
    client = NativeClient(
        host = conf[CONF_HOST].strip(),
        password = conf[CONF_NATIVE_PASSWORD].strip(),
        use_outer_frame = conf[CONF_NATIVE_USE_OUTER_FRAME],
        port = conf[CONF_NATIVE_PORT],
        pin = conf[CONF_NATIVE_PIN].strip() if conf[CONF_NATIVE_USE_CUSTOM_PIN] else None,
    )
    await client.connect()
    await client.initialize()
    try:
        panel_info = client.panel_info
        serial_number = panel_info[0] if panel_info else None
    finally:
        client.disconnect()

    if not serial_number:
        raise ValueError("Native panel did not report a serial number")

    return serial_number


def apply_native_pin_toggle(native_conf: dict) -> dict:
    """Drop the PIN from a submitted native conf when use_custom_pin is unchecked.

    Call this on every user_input dict for the native section before
    storing or testing it -- the checkbox is the source of truth, not
    whether the text field happens to be non-empty.
    """
    result = dict(native_conf)
    if result.get(CONF_NATIVE_USE_CUSTOM_PIN) == False:
        result[CONF_NATIVE_PIN] = None
    return result