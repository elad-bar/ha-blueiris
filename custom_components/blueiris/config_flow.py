"""Config flow to configure BlueIris."""
import logging

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback

from . import get_ha
from .helpers.const import *
from .managers.config_flow_manager import ConfigFlowManager
from .models import AlreadyExistsError, LoginError

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class BlueIrisFlowHandler(config_entries.ConfigFlow):
    """Handle a BlueIris config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        super().__init__()

        self._config_flow = ConfigFlowManager()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        options_handler = BlueIrisOptionsFlowHandler(config_entry)

        return options_handler

    async def async_step_user(self, user_input=None):
        """Handle a flow start."""
        _LOGGER.debug(f"Starting async_step_user of {DOMAIN}")

        errors = None

        self._config_flow.initialize(self.hass)

        if user_input is not None:
            self._config_flow.update_data(user_input, True)

            host = self._config_flow.config_data.host

            ha = get_ha(self.hass, host)

            if ha is None:
                errors = await self._config_flow.valid_login()
            else:
                _LOGGER.warning(f"{DEFAULT_NAME} ({host}) already configured")

                return self.async_abort(
                    reason="already_configured", description_placeholders=user_input
                )

            if errors is None:
                return self.async_create_entry(
                    title=self._config_flow.config_data.host, data=user_input
                )

        data_schema = self._config_flow.get_default_data(user_input)

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_import(self, info):
        """Import existing configuration from BlueIris."""
        _LOGGER.debug(f"Starting async_step_import of {DOMAIN}")
        title = f"{DEFAULT_NAME} (import from configuration.yaml)"

        return self.async_create_entry(title=title, data=info)


class BlueIrisOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle BlueIris options."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize BlueIris options flow."""
        super().__init__()

        self._config_flow = ConfigFlowManager(config_entry)

    async def async_step_init(self, user_input=None):
        """Manage the BlueIris options."""
        return await self.async_step_blue_iris_additional_settings(user_input)

    async def async_step_blue_iris_additional_settings(self, user_input=None):
        errors = None

        self._config_flow.initialize(self.hass)

        if user_input is not None:
            new_user_input = None

            try:
                new_user_input = await self._config_flow.update_options(
                    user_input, True
                )

            except LoginError as lex:
                _LOGGER.warning(f"Cannot complete login")

                errors = lex.errors

            except AlreadyExistsError as aeex:
                new_host = aeex.entry.data.get(CONF_HOST)

                _LOGGER.warning(f"Cannot update host to: {new_host}")

                errors = {"base": "already_configured"}

            if errors is None:
                return self.async_create_entry(title="", data=new_user_input)

        data_schema = self._config_flow.get_default_options()

        return self.async_show_form(
            step_id="blue_iris_additional_settings",
            data_schema=data_schema,
            errors=errors,
            description_placeholders=self._config_flow.data,
        )
