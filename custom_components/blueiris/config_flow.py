"""Config flow to configure BlueIris."""
import logging

import voluptuous as vol
from homeassistant.const import (CONF_SSL, CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD)

from homeassistant import config_entries

from .const import *

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class DahuaVTOFlowHandler(config_entries.ConfigFlow):
    """Handle a BlueIris config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow start."""
        _LOGGER.debug(f"Starting async_step_user of {DOMAIN}")

        if self._async_current_entries():
            return self.async_abort(reason="one_instance_only")

        fields = {
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT): int,
            vol.Optional(CONF_USERNAME): str,
            vol.Optional(CONF_PASSWORD): str,
            vol.Optional(CONF_SSL, default=False): bool,
        }

        if user_input is not None:
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={
                    CONF_HOST: user_input.get(CONF_HOST),
                    CONF_PORT: user_input.get(CONF_PORT, DEFAULT_PORT),
                    CONF_USERNAME: user_input.get(CONF_USERNAME),
                    CONF_PASSWORD: user_input.get(CONF_PASSWORD),
                    CONF_SSL: user_input.get(CONF_SSL)
                },
            )

        return self.async_show_form(step_id="user", data_schema=vol.Schema(fields))

    async def async_step_import(self, info):
        """Import existing configuration from BlueIris."""
        _LOGGER.debug(f"Starting async_step_import of {DOMAIN}")

        if self._async_current_entries():
            return self.async_abort(reason="already_setup")

        return self.async_create_entry(
            title="DahuaVTO (import from configuration.yaml)",
            data={
                CONF_HOST: info.get(CONF_HOST),
                CONF_PORT: info.get(CONF_PORT, DEFAULT_PORT),
                CONF_USERNAME: info.get(CONF_USERNAME),
                CONF_PASSWORD: info.get(CONF_PASSWORD),
                CONF_SSL: info.get(CONF_SSL)
            },
        )
