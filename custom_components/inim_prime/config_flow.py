from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import TextSelector, TextSelectorType, TextSelectorConfig

from inim.prime.primelan.client import InimPrimeClient
from .const import (
    CONF_HOST,
    CONF_API_KEY,
    CONF_USE_HTTPS,
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
    CONF_PANEL_LOG_EVENTS_SCAN_INTERVAL_DEFAULT,
)


def build_connection_schema(
        *,
        default_host: str | None = None,
        default_use_https: bool = True,
        require_api_key: bool = True,
) -> dict:
    """Build the connection schema with optional defaults."""
    schema: dict = {
        vol.Required(
            CONF_HOST,
            default = default_host,
        ): str,
        vol.Required(
            CONF_USE_HTTPS,
            default = default_use_https,
        ): bool,
    }

    if require_api_key:
        schema[vol.Required(CONF_API_KEY)] = TextSelector(
            TextSelectorConfig(type = TextSelectorType.PASSWORD)
        )
    else:
        schema[vol.Optional(CONF_API_KEY)] = TextSelector(
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
    """Build the connection schema with optional defaults."""
    schema: dict = {
        # Panel Log Events Fetch Limit
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
                    # Zones Scan Interval
                    vol.Required(
                        CONF_ZONES_SCAN_INTERVAL,
                        default = default_zones_scan_interval or CONF_ZONES_SCAN_INTERVAL_DEFAULT,
                    ): vol.All(
                        int,
                        vol.Range(min = CONF_SCAN_INTERVAL_MIN, max = CONF_SCAN_INTERVAL_MAX),
                    ),

                    # Partitions Scan Interval
                    vol.Required(
                        CONF_PARTITIONS_SCAN_INTERVAL,
                        default = default_partitions_scan_interval or CONF_PARTITIONS_SCAN_INTERVAL_DEFAULT,
                    ): vol.All(
                        int,
                        vol.Range(min = CONF_SCAN_INTERVAL_MIN, max = CONF_SCAN_INTERVAL_MAX),
                    ),

                    # GSM Scan Interval
                    vol.Required(
                        CONF_GSM_SCAN_INTERVAL,
                        default = default_gsm_scan_interval or CONF_GSM_SCAN_INTERVAL_DEFAULT,
                    ): vol.All(
                        int,
                        vol.Range(min = CONF_SCAN_INTERVAL_MIN, max = CONF_SCAN_INTERVAL_MAX),
                    ),

                    # System Faults Scan Interval
                    vol.Required(
                        CONF_SYSTEM_FAULTS_SCAN_INTERVAL,
                        default = default_system_faults_scan_interval or CONF_SYSTEM_FAULTS_SCAN_INTERVAL_DEFAULT,
                    ): vol.All(
                        int,
                        vol.Range(min = CONF_SCAN_INTERVAL_MIN, max = CONF_SCAN_INTERVAL_MAX),
                    ),

                    # Panel Log Events Scan Interval
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


class InimPrimeOptionsFlowHandler(OptionsFlow):
    """Handle options for the INIM Prime integration."""

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
    VERSION = 1
    MINOR_VERSION = 0

    def __init__(self):
        self._connection_data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Step 1: Connection parameters."""
        errors = {}

        if user_input is not None:
            conf_serial_number: str = user_input[CONF_SERIAL_NUMBER].strip()
            conf_host: str = user_input[CONF_HOST].strip()
            conf_api_key: str = user_input[CONF_API_KEY].strip()
            conf_use_https: bool = user_input.get(CONF_USE_HTTPS, True)

            await self.async_set_unique_id(conf_serial_number)
            self._abort_if_unique_id_configured()

            try:
                client = InimPrimeClient(
                    host = conf_host,
                    api_key = conf_api_key,
                    use_https = conf_use_https,
                )
                await client.connect()
                await client.close()
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                # Save step1 results temporarily
                self._connection_data = {
                    CONF_SERIAL_NUMBER: conf_serial_number,
                    CONF_HOST: conf_host,
                    CONF_API_KEY: conf_api_key,
                    CONF_USE_HTTPS: conf_use_https,
                }

                return await self.async_step_options()

        schema = vol.Schema(
            {
                vol.Required(CONF_SERIAL_NUMBER): str,
                **build_connection_schema(),
            }
        )

        return self.async_show_form(
            step_id = "user",
            data_schema = schema,
            errors = errors,
        )

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        """Step 2: Options / scan intervals."""
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
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            conf_host = user_input[CONF_HOST].strip()
            conf_api_key = user_input.get(CONF_API_KEY, "").strip()
            conf_use_https = user_input[CONF_USE_HTTPS]

            try:
                client = InimPrimeClient(
                    host = conf_host,
                    api_key = conf_api_key or entry.data[CONF_API_KEY],
                    use_https = conf_use_https,
                )
                await client.connect()
                await client.close()
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                # IMPORTANT: update data, reload, abort flow
                data_updates = {
                    CONF_HOST: conf_host,
                    CONF_USE_HTTPS: conf_use_https,
                }

                # Only update API key if user entered a new one
                if conf_api_key:
                    data_updates[CONF_API_KEY] = conf_api_key

                return self.async_update_reload_and_abort(
                    entry,
                    data_updates = data_updates,
                )
        data_schema = vol.Schema(
            {
                **build_connection_schema(
                    default_host = entry.data[CONF_HOST],
                    default_use_https = entry.options.get(CONF_USE_HTTPS, True),
                    require_api_key = False,  # allow leaving it empty
                )
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
