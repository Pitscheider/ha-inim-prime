from __future__ import annotations
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import OptionsFlow

from .models import ConfigOptions
from ..entry_data import get_entry_options, get_entry_data
from .schemas import build_options_schema

class InimPrimeOptionsFlowHandler(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title = "", data = user_input)

        data = get_entry_data(self.config_entry)
        options = get_entry_options(self.config_entry)
        config_options = ConfigOptions(
            zones_scan_interval = options["scan_intervals"]["zones"],
            partitions_scan_interval = options["scan_intervals"]["partitions"],
            gsm_scan_interval = options["scan_intervals"]["gsm"],
            system_faults_scan_interval = options["scan_intervals"]["system_faults"],
            panel_log_events_scan_interval = options["scan_intervals"]["panel_log_events"],
            panel_log_events_fetch_limit = options["panel_log_events_fetch_limit"],
        )


        has_native = bool(data.get("native"))
        has_primelan = bool(data.get("primelan"))

        schema = vol.Schema(
            build_options_schema(
                has_native = has_native,
                has_primelan = has_primelan,
                current_options = config_options,
            )
        )
        return self.async_show_form(step_id = "init", data_schema = schema)