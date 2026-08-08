from __future__ import annotations
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import OptionsFlow

from .schemas import build_options_schema
from ..const import CONF_NATIVE, CONF_PRIMELAN


class InimPrimeOptionsFlowHandler(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
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
        return self.async_show_form(step_id = "init", data_schema = schema)