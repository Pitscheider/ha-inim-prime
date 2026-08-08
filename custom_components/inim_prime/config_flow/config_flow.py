from __future__ import annotations
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback

from .models import NativeConfig, PrimelanConfig, FlowData, OptionsData
from .schemas import build_native_schema, build_primelan_schema, build_connection_schema, build_options_schema
from .connection_test import test_native_connection, test_native_connection_and_get_serial, test_primelan_connection
from .options_flow import InimPrimeOptionsFlowHandler
from ..const import (
    CONF_HOST, CONF_SERIAL_NUMBER, DOMAIN,
    CONF_ZONES_SCAN_INTERVAL, CONF_PARTITIONS_SCAN_INTERVAL, CONF_GSM_SCAN_INTERVAL,
    CONF_SYSTEM_FAULTS_SCAN_INTERVAL, CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT, CONF_NATIVE_USE_OUTER_FRAME_DEFAULT,
    CONF_NATIVE, CONF_PRIMELAN, CONF_NATIVE_PORT, CONF_NATIVE_USE_OUTER_FRAME,
    CONF_NATIVE_PIN, CONF_NATIVE_USE_CUSTOM_PIN, CONF_NATIVE_PASSWORD, CONF_PRIMELAN_API_KEY, CONF_PRIMELAN_USE_HTTPS,
)


@config_entries.HANDLERS.register(DOMAIN)
class InimPrimeConfigFlow(config_entries.ConfigFlow, domain = DOMAIN):
    """Handle a config flow for INIM Prime integration.

    Step order:
      user (menu: native_only / primelan_only / both)
        -> [primelan_only] serial_number (manual entry)
        -> connection (shared host + per-backend options; tests the
           connection(s); Native path retrieves the serial number
           automatically here instead of asking for it)
        -> options (scan intervals, defaults adjusted for whether
           Native is active)
        -> create_entry

    self._data accumulates everything gathered so far and is used both
    to build the final entry and to pre-fill forms if the user is sent
    back to a previous step (the HA frontend keeps step history and
    lets the user navigate back; keeping every step's defaults sourced
    from self._data means resubmitting or coming back doesn't lose data).
    """
    VERSION = 2
    MINOR_VERSION = 0

    def __init__(self):
        self._options: OptionsData = OptionsData()
        self._data: FlowData = FlowData()

    # ------------------------------------------------------------------
    # Step 1: backend choice
    # ------------------------------------------------------------------
    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(
            step_id = "user",
            menu_options = ["native_only", "primelan_only", "both"],
        )

    async def async_step_native_only(self, user_input: dict[str, Any] | None = None):
        self._data.use_native = True
        return await self.async_step_connection()

    async def async_step_primelan_only(self, user_input: dict[str, Any] | None = None):
        self._data.use_primelan = True
        return await self.async_step_serial_number()

    async def async_step_both(self, user_input: dict[str, Any] | None = None):
        self._data.use_native = True
        self._data.use_primelan = True
        return await self.async_step_connection()

    # ------------------------------------------------------------------
    # Step 2 (PrimeLAN-only path): manual serial number
    # ------------------------------------------------------------------
    async def async_step_serial_number(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._data.serial_number = user_input[CONF_SERIAL_NUMBER].strip()
            return await self.async_step_connection()

        schema = vol.Schema(
            {
                vol.Required(CONF_SERIAL_NUMBER, default = self._data.serial_number): str,
            }
        )
        return self.async_show_form(step_id = "serial_number", data_schema = schema)

    # ------------------------------------------------------------------
    # Step 3: connection details (shared host + per-backend sections)
    # ------------------------------------------------------------------
    async def async_step_connection(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.host = user_input[CONF_HOST].strip()
            assert self._data.host is not None

            native_conf = None
            primelan_conf = None

            if self._data.use_native:
                native_conf = user_input[CONF_NATIVE]
                self._data.native = NativeConfig(
                    port = native_conf[CONF_NATIVE_PORT],
                    password = native_conf[CONF_NATIVE_PASSWORD],
                    use_outer_frame = native_conf[CONF_NATIVE_USE_OUTER_FRAME],
                    pin = native_conf[CONF_NATIVE_PIN] if native_conf[CONF_NATIVE_USE_CUSTOM_PIN] else None,
                )

            if self._data.use_primelan:
                primelan_conf = user_input[CONF_PRIMELAN]
                self._data.primelan = PrimelanConfig(
                    api_key = primelan_conf[CONF_PRIMELAN_API_KEY],
                    use_https = primelan_conf[CONF_PRIMELAN_USE_HTTPS],
                )

            try:
                if self._data.use_native:
                    # Native present -> serial number is retrieved here,
                    # never asked to the user.
                    assert self._data.native is not None
                    self._data.serial_number = await test_native_connection_and_get_serial(self._data.native, self._data.host)
                if primelan_conf:
                    assert self._data.primelan is not None
                    await test_primelan_connection(self._data.primelan, self._data.host)
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(self._data.serial_number)
                self._abort_if_unique_id_configured()
                return await self.async_step_options()

        schema = vol.Schema(
            build_connection_schema(
                flow_data = self._data,
            )
        )

        return self.async_show_form(
            step_id = "connection",
            data_schema = schema,
            errors = errors,
        )

    # ------------------------------------------------------------------
    # Step 4: integration options (scan intervals)
    # ------------------------------------------------------------------
    async def async_step_options(self, user_input: dict[str, Any] | None = None):

        if user_input is not None:
            scan_intervals = user_input["scan_intervals"]

            self._options.zones_scan_interval = scan_intervals[CONF_ZONES_SCAN_INTERVAL]
            self._options.partitions_scan_interval = scan_intervals[CONF_PARTITIONS_SCAN_INTERVAL]

            if self._data.use_primelan:
                self._options.gsm_scan_interval = scan_intervals[CONF_GSM_SCAN_INTERVAL]
                self._options.system_faults_scan_interval = scan_intervals[CONF_SYSTEM_FAULTS_SCAN_INTERVAL]
                self._options.panel_log_events_scan_interval = scan_intervals[CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL]
                self._options.panel_log_events_fetch_limit = user_input[CONF_PANEL_LOG_EVENTS_FETCH_LIMIT]

            return self.async_create_entry(
                title = f"INIM Prime ({self._data.serial_number})",
                data = self._data.to_entry_data(),
                options = self._options.to_options_dict(),
            )

        schema = vol.Schema(
            build_options_schema(
                has_native = self._data.use_native,
                has_primelan = self._data.use_primelan,
            )
        )

        return self.async_show_form(step_id = "options", data_schema = schema)

    # ------------------------------------------------------------------
    # Reconfigure (unchanged behaviour, now backed by the shared helpers)
    # ------------------------------------------------------------------
    async def async_step_reconfigure(
            self,
            user_input: dict[str, Any] | None = None
    ):
        """Update connection settings. Both sections optional; leaving a section
        blank in the form keeps the currently-stored config for that backend."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            native_conf = user_input.get(CONF_NATIVE)
            primelan_conf = user_input.get(CONF_PRIMELAN)

            if not native_conf and not primelan_conf:
                errors["base"] = "no_backend_selected"
            else:
                try:
                    if native_conf:
                        test_conf = dict(native_conf)
                        if not test_conf.get("password"):
                            test_conf["password"] = entry.data.get(CONF_NATIVE, {}).get("password")
                        await test_native_connection(test_conf)

                    if primelan_conf:
                        test_conf = dict(primelan_conf)
                        if not test_conf.get("api_key"):
                            test_conf["api_key"] = entry.data.get(CONF_PRIMELAN, {}).get("api_key")
                        await test_primelan_connection(test_conf)
                except Exception:
                    errors["base"] = "cannot_connect"
                else:
                    data_updates: dict[str, Any] = {}

                    if native_conf:
                        native_conf = dict(native_conf)
                        if not native_conf.get("password"):
                            native_conf["password"] = entry.data.get(CONF_NATIVE, {}).get("password")
                        data_updates[CONF_NATIVE] = native_conf
                    else:
                        data_updates[CONF_NATIVE] = None

                    if primelan_conf:
                        primelan_conf = dict(primelan_conf)
                        if not primelan_conf.get("api_key"):
                            primelan_conf["api_key"] = entry.data.get(CONF_PRIMELAN, {}).get("api_key")
                        data_updates[CONF_PRIMELAN] = primelan_conf
                    else:
                        data_updates[CONF_PRIMELAN] = None

                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates = data_updates,
                    )

        native_defaults = entry.data.get(CONF_NATIVE) or {}
        primelan_defaults = entry.data.get(CONF_PRIMELAN) or {}

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_NATIVE): build_native_schema(
                    default_host = native_defaults.get(CONF_HOST),
                    default_port = native_defaults.get("port"),
                    default_use_outer_frame = native_defaults.get(
                        "use_outer_frame", CONF_NATIVE_USE_OUTER_FRAME_DEFAULT
                    ),
                    require_password = False,
                ) and vol.Schema(
                    build_native_schema(
                        default_host = native_defaults.get(CONF_HOST),
                        default_port = native_defaults.get("port"),
                        default_use_outer_frame = native_defaults.get(
                            "use_outer_frame", CONF_NATIVE_USE_OUTER_FRAME_DEFAULT
                        ),
                        require_password = False,
                    )
                ),
                vol.Optional(CONF_PRIMELAN): vol.Schema(
                    build_primelan_schema(
                        default_host = primelan_defaults.get(CONF_HOST),
                        default_use_https = primelan_defaults.get("use_https", True),
                        require_api_key = False,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id = "reconfigure",
            data_schema = data_schema,
            errors = errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
            config_entry: ConfigEntry,
    ) -> InimPrimeOptionsFlowHandler:
        return InimPrimeOptionsFlowHandler()