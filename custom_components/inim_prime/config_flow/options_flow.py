from __future__ import annotations
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import OptionsFlow

from inim_prime import get_entry_options
from ..custom_types import get_entry_data
from .schemas import build_options_schema

class InimPrimeOptionsFlowHandler(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title = "", data = user_input)

        data = get_entry_data(self.config_entry)
        options = get_entry_options(self.config_entry)

        has_native = bool(data.get("native"))
        has_primelan = bool(data.get("primelan"))

        schema = vol.Schema(
            build_options_schema(
                has_native = has_native,
                has_primelan = has_primelan,
                current_options = options,
            )
        )
        return self.async_show_form(step_id = "init", data_schema = schema)