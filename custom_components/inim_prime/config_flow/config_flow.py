from __future__ import annotations
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback

from ..const import DOMAIN
from .const import (
    DataKey,
    OptionsKey,
)
from .models import NativeConfig, PrimelanConfig, FlowData, OptionsData
from .schemas import build_native_schema, build_primelan_schema, build_connection_schema, build_options_schema
from .connection_test import test_native_connection, test_native_connection_and_get_serial, test_primelan_connection
from .options_flow import InimPrimeOptionsFlowHandler


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
            self._data.serial_number = user_input[DataKey.SERIAL_NUMBER].strip()
            return await self.async_step_connection()

        schema = vol.Schema(
            {
                vol.Required(DataKey.SERIAL_NUMBER, default = self._data.serial_number): str,
            }
        )
        return self.async_show_form(step_id = "serial_number", data_schema = schema)

    # ------------------------------------------------------------------
    # Step 3: connection details (shared host + per-backend sections)
    # ------------------------------------------------------------------
    async def async_step_connection(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.host = user_input[DataKey.HOST].strip()
            assert self._data.host is not None

            if self._data.use_native:
                native_conf = user_input[DataKey.NATIVE]
                self._data.native = NativeConfig(
                    port = native_conf[DataKey.Native.PORT],
                    password = native_conf[DataKey.Native.PASSWORD],
                    use_outer_frame = native_conf[DataKey.Native.USE_OUTER_FRAME],
                    pin = native_conf[DataKey.Native.PIN] if native_conf[DataKey.Native.USE_CUSTOM_PIN] else None,
                )

            if self._data.use_primelan:
                primelan_conf = user_input[DataKey.PRIMELAN]
                self._data.primelan = PrimelanConfig(
                    api_key = primelan_conf[DataKey.Primelan.API_KEY],
                    use_https = primelan_conf[DataKey.Primelan.USE_HTTPS],
                )

            try:
                if self._data.native is not None:
                    # Native present -> serial number is retrieved here,
                    # never asked to the user.
                    self._data.serial_number = await test_native_connection_and_get_serial(self._data.native, self._data.host)

                if self._data.primelan is not None:
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

            self._options.zones_scan_interval = scan_intervals[OptionsKey.ScanIntervals.ZONES]
            self._options.partitions_scan_interval = scan_intervals[OptionsKey.ScanIntervals.PARTITIONS]

            if self._data.use_primelan:
                self._options.gsm_scan_interval = scan_intervals[OptionsKey.ScanIntervals.GSM]
                self._options.system_faults_scan_interval = scan_intervals[OptionsKey.ScanIntervals.SYSTEM_FAULTS]
                self._options.panel_log_events_scan_interval = scan_intervals[OptionsKey.ScanIntervals.PANEL_LOG_EVENTS]
                self._options.panel_log_events_fetch_limit = user_input[OptionsKey.PANEL_LOG_EVENTS_FETCH_LIMIT]

            assert self._data.serial_number is not None
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

    @staticmethod
    @callback
    def async_get_options_flow(
            config_entry: ConfigEntry,
    ) -> InimPrimeOptionsFlowHandler:
        return InimPrimeOptionsFlowHandler()