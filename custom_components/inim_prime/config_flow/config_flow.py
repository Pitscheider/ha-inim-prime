from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback

from .connection_test import test_native_connection, test_native_connection_and_get_serial, test_primelan_connection
from .const import (
    DataKey,
    OptionsKey,
)
from .models import NativeConfig, PrimelanConfig, ConfigData, ConfigOptions
from .options_flow import InimPrimeOptionsFlowHandler
from .schemas import build_connection_schema, build_options_schema
from ..const import DOMAIN
from ..entry_data import get_entry_data, get_entry_options


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
        self._options: ConfigOptions = ConfigOptions()
        self._data: ConfigData = ConfigData()

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



    # ==================================================================
    # Reconfigure flow
    # ==================================================================
    # Entry point invoked by HA when the user picks "Reconfigure" on an
    # existing entry. Mirrors the initial-setup flow above, minus the
    # serial_number step: the panel is already identified, so its serial
    # number is carried over from the existing entry and never re-asked
    # or re-fetched.
    # ------------------------------------------------------------------

    def _init_data_from_entry(self, entry: ConfigEntry) -> None:
        """Pre-fill self._data with the entry's current configuration."""
        data = get_entry_data(entry)
        self._data.serial_number = data["serial_number"]
        self._data.host = data["host"]

        native_conf = data.get("native")
        if native_conf:
            self._data.use_native = True
            self._data.native = NativeConfig(
                port = native_conf["port"],
                password = native_conf["password"],
                use_outer_frame = native_conf["use_outer_frame"],
                pin = native_conf["pin"],
            )

        primelan_conf = data.get("primelan")
        if primelan_conf:
            self._data.use_primelan = True
            self._data.primelan = PrimelanConfig(
                api_key = primelan_conf["api_key"],
                use_https = primelan_conf["use_https"],
            )

    def _init_options_from_entry(self, entry: ConfigEntry) -> None:
        """Pre-fill self._options with the entry's current options."""
        options = get_entry_options(entry)
        scan_intervals = options["scan_intervals"]

        self._options.zones_scan_interval = scan_intervals.get("zones")
        self._options.partitions_scan_interval = scan_intervals.get("partitions")
        self._options.gsm_scan_interval = scan_intervals.get("gsm")
        self._options.system_faults_scan_interval = scan_intervals.get("system_faults")
        self._options.panel_log_events_scan_interval = scan_intervals.get("panel_log_events")
        self._options.panel_log_events_fetch_limit = options.get("panel_log_events_fetch_limit")

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        # Populate self._data/self._options from the existing entry only
        # once (first time this flow instance reaches this step).
        if self._data.serial_number is None:
            reconfigure_entry = self._get_reconfigure_entry()
            self._init_data_from_entry(reconfigure_entry)
            self._init_options_from_entry(reconfigure_entry)

        return self.async_show_menu(
            step_id = "reconfigure",
            menu_options = ["reconfigure_native_only", "reconfigure_primelan_only", "reconfigure_both"],
        )

    async def async_step_reconfigure_native_only(self, user_input: dict[str, Any] | None = None):
        self._data.use_native = True
        self._data.use_primelan = False
        self._data.primelan = None
        return await self.async_step_reconfigure_connection()

    async def async_step_reconfigure_primelan_only(self, user_input: dict[str, Any] | None = None):
        self._data.use_native = False
        self._data.use_primelan = True
        self._data.native = None
        return await self.async_step_reconfigure_connection()

    async def async_step_reconfigure_both(self, user_input: dict[str, Any] | None = None):
        self._data.use_native = True
        self._data.use_primelan = True
        return await self.async_step_reconfigure_connection()

    async def async_step_reconfigure_connection(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.host = user_input[DataKey.HOST].strip()
            assert self._data.host is not None

            if self._data.use_native:
                assert self._data.native is not None
                native_conf = user_input[DataKey.NATIVE]
                new_password = native_conf[DataKey.Native.PASSWORD] if native_conf.get(DataKey.Native.PASSWORD) is not None else self._data.native.password
                new_pin = None
                if native_conf.get(DataKey.Native.USE_CUSTOM_PIN):
                    new_pin = native_conf[DataKey.Native.PIN] if native_conf.get(DataKey.Native.PIN) is not None else self._data.native.pin

                self._data.native = NativeConfig(
                    port = native_conf[DataKey.Native.PORT],
                    password = new_password,
                    use_outer_frame = native_conf[DataKey.Native.USE_OUTER_FRAME],
                    pin = new_pin,
                )

            if self._data.use_primelan:
                assert self._data.primelan is not None
                primelan_conf = user_input[DataKey.PRIMELAN]
                self._data.primelan = PrimelanConfig(
                    api_key = primelan_conf[DataKey.Primelan.API_KEY] if primelan_conf.get(DataKey.Primelan.API_KEY) is not None else self._data.primelan.api_key,
                    use_https = primelan_conf[DataKey.Primelan.USE_HTTPS],
                )

            try:
                if self._data.native is not None:
                    # Reconfigure never touches the serial number -- it's
                    # carried over from the existing entry, only the
                    # connection itself is verified here.
                    await test_native_connection(self._data.native, self._data.host)

                if self._data.primelan is not None:
                    await test_primelan_connection(self._data.primelan, self._data.host)

            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_reconfigure_options()

        schema = vol.Schema(
            build_connection_schema(
                flow_data = self._data,
            )
        )

        return self.async_show_form(
            step_id = "reconfigure_connection",
            data_schema = schema,
            errors = errors,
        )

    async def async_step_reconfigure_options(self, user_input: dict[str, Any] | None = None):

        if user_input is not None:
            scan_intervals = user_input["scan_intervals"]

            self._options.zones_scan_interval = scan_intervals[OptionsKey.ScanIntervals.ZONES]
            self._options.partitions_scan_interval = scan_intervals[OptionsKey.ScanIntervals.PARTITIONS]

            if self._data.use_primelan:
                self._options.gsm_scan_interval = scan_intervals[OptionsKey.ScanIntervals.GSM]
                self._options.system_faults_scan_interval = scan_intervals[OptionsKey.ScanIntervals.SYSTEM_FAULTS]
                self._options.panel_log_events_scan_interval = scan_intervals[OptionsKey.ScanIntervals.PANEL_LOG_EVENTS]
                self._options.panel_log_events_fetch_limit = user_input[OptionsKey.PANEL_LOG_EVENTS_FETCH_LIMIT]
            else:
                # Backend switched away from PrimeLAN: drop its
                # PrimeLAN-only options rather than leaving stale values
                # from the entry this flow was pre-filled from.
                self._options.gsm_scan_interval = None
                self._options.system_faults_scan_interval = None
                self._options.panel_log_events_scan_interval = None
                self._options.panel_log_events_fetch_limit = None

            assert self._data.serial_number is not None
            reconfigure_entry = self._get_reconfigure_entry()
            return self.async_update_reload_and_abort(
                reconfigure_entry,
                title = f"INIM Prime ({self._data.serial_number})",
                data = self._data.to_entry_data(),
                options = self._options.to_options_dict(),
            )

        schema = vol.Schema(
            build_options_schema(
                has_native = self._data.use_native,
                has_primelan = self._data.use_primelan,
                current_options = self._options,
            )
        )

        return self.async_show_form(step_id = "reconfigure_options", data_schema = schema)