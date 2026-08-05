from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import TextSelector, TextSelectorType, TextSelectorConfig

from inim.prime.native.client import Client as NativeClient
from inim.prime.primelan.client import InimPrimeClient

from .const import (
    CONF_HOST,
    CONF_PRIMELAN_API_KEY,
    CONF_PRIMELAN_USE_HTTPS,
    CONF_SERIAL_NUMBER,
    DOMAIN,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_DEFAULT,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MIN,
    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MAX,
    CONF_SCAN_INTERVAL_MIN,
    CONF_SCAN_INTERVAL_MAX,

    # --- Scan interval config keys ---
    CONF_ZONES_SCAN_INTERVAL,
    CONF_PARTITIONS_SCAN_INTERVAL,
    CONF_GSM_SCAN_INTERVAL,
    CONF_SYSTEM_FAULTS_SCAN_INTERVAL,
    CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL,

    # --- Defaults (custom per coordinator) ---
    CONF_ZONES_SCAN_INTERVAL_DEFAULT,
    CONF_PARTITIONS_SCAN_INTERVAL_DEFAULT,
    CONF_GSM_SCAN_INTERVAL_DEFAULT,
    CONF_SYSTEM_FAULTS_SCAN_INTERVAL_DEFAULT,
    CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL_DEFAULT, CONF_NATIVE_USE_OUTER_FRAME_DEFAULT, CONF_NATIVE_PORT,
    CONF_NATIVE_PORT_DEFAULT, CONF_NATIVE_USE_OUTER_FRAME, CONF_NATIVE_PIN, CONF_NATIVE_PASSWORD, CONF_NATIVE,
    CONF_PRIMELAN,
)

def build_native_schema(
        *,
        default_host: str | None = None,
        default_port: int | None = None,
        default_use_outer_frame: bool = CONF_NATIVE_USE_OUTER_FRAME_DEFAULT,
        require_password: bool = True,
) -> dict:
    """Build the native-protocol connection schema with optional defaults."""
    schema: dict = {
        vol.Required(CONF_HOST, default = default_host): str,
        vol.Required(CONF_NATIVE_PORT, default = default_port or CONF_NATIVE_PORT_DEFAULT): int,
        vol.Required(CONF_NATIVE_USE_OUTER_FRAME, default = default_use_outer_frame): bool,
        vol.Optional(CONF_NATIVE_PIN): TextSelector(TextSelectorConfig(type = TextSelectorType.PASSWORD)),
    }

    if require_password:
        schema[vol.Required(CONF_NATIVE_PASSWORD)] = TextSelector(
            TextSelectorConfig(type = TextSelectorType.PASSWORD)
        )
    else:
        schema[vol.Optional(CONF_NATIVE_PASSWORD)] = TextSelector(
            TextSelectorConfig(type = TextSelectorType.PASSWORD)
        )

    return schema


def build_primelan_schema(
        *,
        default_host: str | None = None,
        default_use_https: bool = True,
        require_api_key: bool = True,
) -> dict:
    """Build the PrimeLAN connection schema with optional defaults."""
    schema: dict = {
        vol.Required(
            CONF_HOST,
            default = default_host,
        ): str,
        vol.Required(
            CONF_PRIMELAN_USE_HTTPS,
            default = default_use_https,
        ): bool,
    }

    if require_api_key:
        schema[vol.Required(CONF_PRIMELAN_API_KEY)] = TextSelector(
            TextSelectorConfig(type = TextSelectorType.PASSWORD)
        )
    else:
        schema[vol.Optional(CONF_PRIMELAN_API_KEY)] = TextSelector(
            TextSelectorConfig(type = TextSelectorType.PASSWORD)
        )

    return schema


def build_optional_schema(
        *,
        default_panel_log_events_fetch_limit: int | None = None,
        default_zones_scan_interval: int | None = None,
        default_partitions_scan_interval: int | None = None,
        default_gsm_scan_interval: int | None = None,
        default_system_faults_scan_interval: int | None = None,
        default_panel_log_events_scan_interval: int | None = None,
) -> dict:
    """Build the options schema with optional defaults. Unchanged from before --
    scan intervals / log fetch limit are generic and apply regardless of backend."""
    schema: dict = {
        vol.Required(
            schema = CONF_PANEL_LOG_EVENTS_FETCH_LIMIT,
            default = default_panel_log_events_fetch_limit or CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_DEFAULT,
        ): vol.All(
            int,
            vol.Range(
                min = CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MIN,
                max = CONF_PANEL_LOG_EVENTS_FETCH_LIMIT_MAX,
            ),
        ),
        vol.Required("scan_intervals"): section(
            vol.Schema(
                {
                    vol.Required(
                        CONF_ZONES_SCAN_INTERVAL,
                        default = default_zones_scan_interval or CONF_ZONES_SCAN_INTERVAL_DEFAULT,
                    ): vol.All(
                        int,
                        vol.Range(min = CONF_SCAN_INTERVAL_MIN, max = CONF_SCAN_INTERVAL_MAX),
                    ),
                    vol.Required(
                        CONF_PARTITIONS_SCAN_INTERVAL,
                        default = default_partitions_scan_interval or CONF_PARTITIONS_SCAN_INTERVAL_DEFAULT,
                    ): vol.All(
                        int,
                        vol.Range(min = CONF_SCAN_INTERVAL_MIN, max = CONF_SCAN_INTERVAL_MAX),
                    ),
                    vol.Required(
                        CONF_GSM_SCAN_INTERVAL,
                        default = default_gsm_scan_interval or CONF_GSM_SCAN_INTERVAL_DEFAULT,
                    ): vol.All(
                        int,
                        vol.Range(min = CONF_SCAN_INTERVAL_MIN, max = CONF_SCAN_INTERVAL_MAX),
                    ),
                    vol.Required(
                        CONF_SYSTEM_FAULTS_SCAN_INTERVAL,
                        default = default_system_faults_scan_interval or CONF_SYSTEM_FAULTS_SCAN_INTERVAL_DEFAULT,
                    ): vol.All(
                        int,
                        vol.Range(min = CONF_SCAN_INTERVAL_MIN, max = CONF_SCAN_INTERVAL_MAX),
                    ),
                    vol.Required(
                        CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL,
                        default = default_panel_log_events_scan_interval or CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL_DEFAULT,
                    ): vol.All(
                        int,
                        vol.Range(
                            min = CONF_SCAN_INTERVAL_MIN,
                            max = CONF_SCAN_INTERVAL_MAX,
                        ),
                    ),
                }
            ),
        ),
    }

    return schema

async def _test_native_connection(conf: dict) -> None:
    client = NativeClient(
        host = conf[CONF_HOST].strip(),
        password = conf[CONF_NATIVE_PASSWORD].strip(),
        use_outer_frame = conf[CONF_NATIVE_USE_OUTER_FRAME],
        port = conf[CONF_NATIVE_PORT],
        pin = (conf.get(CONF_NATIVE_PIN) or "").strip() or None,
    )
    await client.connect()
    await client.initialize()
    client.disconnect()


async def _test_primelan_connection(conf: dict) -> None:
    client = InimPrimeClient(
        host = conf[CONF_HOST].strip(),
        api_key = conf[CONF_PRIMELAN_API_KEY].strip(),
        use_https = conf.get(CONF_PRIMELAN_USE_HTTPS, True),
    )
    await client.connect()
    await client.close()


class InimPrimeOptionsFlowHandler(OptionsFlow):
    """Handle options for the INIM Prime integration. Unchanged from before."""

    async def async_step_init(
            self,
            user_input: dict[str, Any] | None = None,
    ):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title = "", data = user_input)

        schema = vol.Schema(
            {
                **build_optional_schema(
                    default_zones_scan_interval = self.config_entry.options.get(
                        CONF_ZONES_SCAN_INTERVAL,
                        None,
                    ),
                    default_partitions_scan_interval = self.config_entry.options.get(
                        CONF_PARTITIONS_SCAN_INTERVAL,
                        None,
                    ),
                    default_gsm_scan_interval = self.config_entry.options.get(
                        CONF_GSM_SCAN_INTERVAL,
                        None,
                    ),
                    default_system_faults_scan_interval = self.config_entry.options.get(
                        CONF_SYSTEM_FAULTS_SCAN_INTERVAL,
                        None,
                    ),
                    default_panel_log_events_scan_interval = self.config_entry.options.get(
                        CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL,
                        None,
                    ),
                    default_panel_log_events_fetch_limit = self.config_entry.options.get(
                        CONF_PANEL_LOG_EVENTS_FETCH_LIMIT,
                        None,
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id = "init",
            data_schema = schema,
        )


@config_entries.HANDLERS.register(DOMAIN)
class InimPrimeConfigFlow(config_entries.ConfigFlow, domain = DOMAIN):
    """Handle a config flow for INIM Prime integration."""
    VERSION = 2
    MINOR_VERSION = 0

    def __init__(self):
        self._connection_data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Step 1: serial number + at least one of native / primelan connection blocks."""
        errors: dict[str, str] = {}

        if user_input is not None:
            conf_serial_number: str = user_input[CONF_SERIAL_NUMBER].strip()
            native_conf = user_input.get(CONF_NATIVE)
            primelan_conf = user_input.get(CONF_PRIMELAN)

            if not native_conf and not primelan_conf:
                errors["base"] = "no_backend_selected"
            else:
                await self.async_set_unique_id(conf_serial_number)
                self._abort_if_unique_id_configured()

                try:
                    if native_conf:
                        await _test_native_connection(native_conf)
                    if primelan_conf:
                        await _test_primelan_connection(primelan_conf)
                except Exception:
                    errors["base"] = "cannot_connect"
                else:
                    self._connection_data = {CONF_SERIAL_NUMBER: conf_serial_number}
                    if native_conf:
                        self._connection_data[CONF_NATIVE] = native_conf
                    if primelan_conf:
                        self._connection_data[CONF_PRIMELAN] = primelan_conf

                    return await self.async_step_options()

        schema = vol.Schema(
            {
                vol.Required(CONF_SERIAL_NUMBER): str,
                vol.Optional(CONF_NATIVE): section(vol.Schema(build_native_schema())),
                vol.Optional(CONF_PRIMELAN): section(vol.Schema(build_primelan_schema())),
            }
        )

        return self.async_show_form(
            step_id = "user",
            data_schema = schema,
            errors = errors,
        )

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        """Step 2: Options / scan intervals. Unchanged from before."""
        if user_input is not None:
            scan_intervals = user_input["scan_intervals"]

            return self.async_create_entry(
                title = f"INIM Prime ({self._connection_data[CONF_SERIAL_NUMBER]})",
                data = self._connection_data,
                options = {
                    CONF_PANEL_LOG_EVENTS_FETCH_LIMIT: user_input[CONF_PANEL_LOG_EVENTS_FETCH_LIMIT],
                    CONF_ZONES_SCAN_INTERVAL: scan_intervals[CONF_ZONES_SCAN_INTERVAL],
                    CONF_PARTITIONS_SCAN_INTERVAL: scan_intervals[CONF_PARTITIONS_SCAN_INTERVAL],
                    CONF_GSM_SCAN_INTERVAL: scan_intervals[CONF_GSM_SCAN_INTERVAL],
                    CONF_SYSTEM_FAULTS_SCAN_INTERVAL: scan_intervals[CONF_SYSTEM_FAULTS_SCAN_INTERVAL],
                    CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL: scan_intervals[CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL],
                },
            )

        schema = vol.Schema(
            {
                **build_optional_schema(),
            }
        )

        return self.async_show_form(
            step_id = "options",
            data_schema = schema,
        )

    async def async_step_reconfigure(
            self,
            user_input: dict[str, Any] | None = None
    ):
        """Update connection settings. Both sections optional; leaving a section
        blank in the form keeps the currently-stored config for that backend
        (matches the original 'leave API key blank to keep current' pattern,
        extended to whole sections)."""
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
                        if not test_conf.get(CONF_NATIVE_PASSWORD):
                            test_conf[CONF_NATIVE_PASSWORD] = entry.data.get(CONF_NATIVE, {}).get(CONF_NATIVE_PASSWORD)
                        await _test_native_connection(test_conf)

                    if primelan_conf:
                        test_conf = dict(primelan_conf)
                        if not test_conf.get(CONF_PRIMELAN_API_KEY):
                            test_conf[CONF_PRIMELAN_API_KEY] = entry.data.get(CONF_PRIMELAN, {}).get(CONF_PRIMELAN_API_KEY)
                        await _test_primelan_connection(test_conf)
                except Exception:
                    errors["base"] = "cannot_connect"
                else:
                    data_updates: dict[str, Any] = {}

                    if native_conf:
                        native_conf = dict(native_conf)
                        if not native_conf.get(CONF_NATIVE_PASSWORD):
                            native_conf[CONF_NATIVE_PASSWORD] = entry.data.get(CONF_NATIVE, {}).get(CONF_NATIVE_PASSWORD)
                        data_updates[CONF_NATIVE] = native_conf
                    else:
                        # Leaving this section empty disables/removes native.
                        # NOTE: this sets the key to None rather than deleting
                        # it outright -- functionally equivalent (the gateway
                        # treats a falsy "native" block as "not configured"),
                        # but worth knowing if you inspect entry.data directly.
                        data_updates[CONF_NATIVE] = None

                    if primelan_conf:
                        primelan_conf = dict(primelan_conf)
                        if not primelan_conf.get(CONF_PRIMELAN_API_KEY):
                            primelan_conf[CONF_PRIMELAN_API_KEY] = entry.data.get(CONF_PRIMELAN, {}).get(CONF_PRIMELAN_API_KEY)
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
                vol.Optional(CONF_NATIVE): section(
                    vol.Schema(
                        build_native_schema(
                            default_host = native_defaults.get(CONF_HOST),
                            default_port = native_defaults.get(CONF_NATIVE_PORT),
                            default_use_outer_frame = native_defaults.get(
                                CONF_NATIVE_USE_OUTER_FRAME, CONF_NATIVE_USE_OUTER_FRAME_DEFAULT
                            ),
                            require_password = False,
                        )
                    )
                ),
                vol.Optional(CONF_PRIMELAN): section(
                    vol.Schema(
                        build_primelan_schema(
                            default_host = primelan_defaults.get(CONF_HOST),
                            default_use_https = primelan_defaults.get(CONF_PRIMELAN_USE_HTTPS, True),
                            require_api_key = False,
                        )
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
        """Return the options flow handler for this integration."""
        return InimPrimeOptionsFlowHandler()

