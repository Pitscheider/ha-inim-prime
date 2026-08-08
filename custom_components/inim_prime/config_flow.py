from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback

from .config_flow_helpers import (
    build_native_schema,
    build_primelan_schema,
    build_connection_schema,
    build_options_schema,
    test_native_connection,
    test_native_connection_and_get_serial,
    test_primelan_connection,
)
from .const import (
    CONF_HOST,
    CONF_SERIAL_NUMBER,
    DOMAIN,
    CONF_ZONES_SCAN_INTERVAL,
    CONF_PARTITIONS_SCAN_INTERVAL,
    CONF_GSM_SCAN_INTERVAL,
    CONF_SYSTEM_FAULTS_SCAN_INTERVAL,
    CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT,
    CONF_NATIVE_USE_OUTER_FRAME_DEFAULT,
    CONF_NATIVE,
    CONF_PRIMELAN,
)


class InimPrimeOptionsFlowHandler(OptionsFlow):
    """Handle post-setup options for the INIM Prime integration."""

    async def async_step_init(
            self,
            user_input: dict[str, Any] | None = None,
    ):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title = "", data = user_input)

        has_native = bool(self.config_entry.data.get(CONF_NATIVE))
        has_primelan = bool(self.config_entry.data.get(CONF_PRIMELAN))

        schema = vol.Schema(
            build_options_schema(
                has_native = has_native,
                has_primelan = has_primelan,
                defaults = self.config_entry.options,
            )
        )

        return self.async_show_form(
            step_id = "init",
            data_schema = schema,
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
        self._data: dict[str, Any] = {}
        self._backends: set[str] = set()

    # ------------------------------------------------------------------
    # Step 1: backend choice
    # ------------------------------------------------------------------
    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(
            step_id = "user",
            menu_options = ["native_only", "primelan_only", "both"],
        )

    async def async_step_native_only(self, user_input: dict[str, Any] | None = None):
        self._backends = {CONF_NATIVE}
        return await self.async_step_connection()

    async def async_step_primelan_only(self, user_input: dict[str, Any] | None = None):
        self._backends = {CONF_PRIMELAN}
        return await self.async_step_serial_number()

    async def async_step_both(self, user_input: dict[str, Any] | None = None):
        self._backends = {CONF_NATIVE, CONF_PRIMELAN}
        return await self.async_step_connection()

    # ------------------------------------------------------------------
    # Step 2 (PrimeLAN-only path): manual serial number
    # ------------------------------------------------------------------
    async def async_step_serial_number(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._data[CONF_SERIAL_NUMBER] = user_input[CONF_SERIAL_NUMBER].strip()
            return await self.async_step_connection()

        schema = vol.Schema(
            {
                vol.Required(CONF_SERIAL_NUMBER, default = self._data.get(CONF_SERIAL_NUMBER)): str,
            }
        )
        return self.async_show_form(step_id = "serial_number", data_schema = schema)

    # ------------------------------------------------------------------
    # Step 3: connection details (shared host + per-backend sections)
    # ------------------------------------------------------------------
    async def async_step_connection(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            self._data[CONF_HOST] = host

            native_conf = None
            primelan_conf = None

            if CONF_NATIVE in self._backends:
                native_conf = {**user_input[CONF_NATIVE], CONF_HOST: host}
                self._data[CONF_NATIVE] = native_conf

            if CONF_PRIMELAN in self._backends:
                primelan_conf = {**user_input[CONF_PRIMELAN], CONF_HOST: host}
                self._data[CONF_PRIMELAN] = primelan_conf

            try:
                if native_conf:
                    # Native present -> serial number is retrieved here,
                    # never asked to the user.
                    self._data[CONF_SERIAL_NUMBER] = await test_native_connection_and_get_serial(native_conf)
                if primelan_conf:
                    await test_primelan_connection(primelan_conf)
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(self._data[CONF_SERIAL_NUMBER])
                self._abort_if_unique_id_configured()
                return await self.async_step_options()

        schema = vol.Schema(
            build_connection_schema(
                backends = self._backends,
                default_host = self._data.get(CONF_HOST),
                native_defaults = self._data.get(CONF_NATIVE),
                primelan_defaults = self._data.get(CONF_PRIMELAN),
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
        has_native = CONF_NATIVE in self._backends
        has_primelan = CONF_PRIMELAN in self._backends

        if user_input is not None:
            scan_intervals = user_input["scan_intervals"]

            options: dict[str, Any] = {
                CONF_ZONES_SCAN_INTERVAL: scan_intervals[CONF_ZONES_SCAN_INTERVAL],
                CONF_PARTITIONS_SCAN_INTERVAL: scan_intervals[CONF_PARTITIONS_SCAN_INTERVAL],
            }

            if has_primelan:
                options[CONF_GSM_SCAN_INTERVAL] = scan_intervals[CONF_GSM_SCAN_INTERVAL]
                options[CONF_SYSTEM_FAULTS_SCAN_INTERVAL] = scan_intervals[CONF_SYSTEM_FAULTS_SCAN_INTERVAL]
                options[CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL] = scan_intervals[CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL]
                options[CONF_PANEL_LOG_EVENTS_FETCH_LIMIT] = user_input[CONF_PANEL_LOG_EVENTS_FETCH_LIMIT]

            entry_data: dict[str, Any] = {CONF_SERIAL_NUMBER: self._data[CONF_SERIAL_NUMBER]}
            if has_native:
                entry_data[CONF_NATIVE] = self._data[CONF_NATIVE]
            if has_primelan:
                entry_data[CONF_PRIMELAN] = self._data[CONF_PRIMELAN]

            return self.async_create_entry(
                title = f"INIM Prime ({self._data[CONF_SERIAL_NUMBER]})",
                data = entry_data,
                options = options,
            )

        schema = vol.Schema(
            build_options_schema(
                has_native = has_native,
                has_primelan = has_primelan,
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