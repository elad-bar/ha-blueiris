"""Config flow to configure BlueIris."""
import copy
import logging

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback

from .password_manager import PasswordManager
from .blue_iris_api import BlueIrisApi
from .const import *

_LOGGER = logging.getLogger(__name__)


async def _valid_login(hass, host, port, is_ssl, username, password):
    errors = None

    api = BlueIrisApi(hass, host, port, is_ssl)
    await api.initialize(username, password)

    if not api.is_logged_in:
        _LOGGER.warning(f"Failed to access BlueIris Server ({host})")
        errors = {
            "base": "invalid_server_details"
        }
    else:
        has_credentials = len(username) > 0 or len(password) > 0

        if has_credentials and not api.data.get("admin", False):
            _LOGGER.warning(f"Failed to login BlueIris ({host}) due to invalid credentials")
            errors = {
                "base": "invalid_admin_credentials"
            }

    return {
        "logged-in": errors is None,
        "errors": errors
    }


@config_entries.HANDLERS.register(DOMAIN)
class BlueIrisFlowHandler(config_entries.ConfigFlow):
    """Handle a BlueIris config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return BlueIrisOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow start."""
        _LOGGER.debug(f"Starting async_step_user of {DOMAIN}")

        if self._async_current_entries():
            return self.async_abort(reason="one_instance_only")

        errors = None
        host = None

        if user_input is not None:
            host = user_input.get(CONF_HOST)
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            is_ssl = user_input.get(CONF_SSL)
            username = user_input.get(CONF_USERNAME, "")
            password = user_input.get(CONF_PASSWORD, "")

            if len(password) > 0:
                password_manager = PasswordManager(self.hass)
                password = password_manager.encrypt(password)

                user_input[CONF_PASSWORD] = password

            result = await _valid_login(self.hass, host, port, is_ssl, username, password)
            errors = result.get("errors")

        if host is not None and errors is None:
            return self.async_create_entry(title=host, data=user_input)

        return self.async_show_form(step_id="user", data_schema=vol.Schema(CONFIG_FIELDS), errors=errors)

    async def async_step_import(self, info):
        """Import existing configuration from BlueIris."""
        _LOGGER.debug(f"Starting async_step_import of {DOMAIN}")

        if self._async_current_entries():
            return self.async_abort(reason="already_setup")

        return self.async_create_entry(
            title="BlueIris (import from configuration.yaml)",
            data={
                CONF_HOST: info.get(CONF_HOST),
                CONF_PORT: info.get(CONF_PORT, DEFAULT_PORT),
                CONF_USERNAME: info.get(CONF_USERNAME, ""),
                CONF_PASSWORD: info.get(CONF_PASSWORD, ""),
                CONF_SSL: info.get(CONF_SSL)
            },
        )


class BlueIrisOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle BlueIris options."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize EdgeOS options flow."""
        self.options = copy.deepcopy(config_entry.options)
        self._data = copy.deepcopy(config_entry.data)

    async def async_step_init(self, user_input=None):
        """Manage the EdgeOS options."""
        return await self.async_step_blue_iris_additional_settings(user_input)

    def get_value(self, key, default=None):
        if default is None:
            default = ""

        value = self._data.get(key, default)

        if key in self.options:
            value = self.options.get(key, False)

        return value

    async def async_step_blue_iris_additional_settings(self, user_input=None):
        errors = None

        if user_input is not None:
            username = ""
            password = ""
            clear_credentials = user_input.get(CONF_CLEAR_CREDENTIALS, False)

            if not clear_credentials:
                username = user_input.get(CONF_USERNAME, "")
                password = user_input.get(CONF_PASSWORD, "")

                if len(password) > 0:
                    password_manager = PasswordManager(self.hass)
                    password = password_manager.encrypt(password)

                    user_input[CONF_PASSWORD] = password

            self.options[CONF_USERNAME] = username
            self.options[CONF_PASSWORD] = password
            self.options[CONF_EXCLUDE_SYSTEM_CAMERA] = user_input.get(CONF_EXCLUDE_SYSTEM_CAMERA, False)

            host = self._data.get(CONF_HOST)
            port = self._data.get(CONF_PORT)
            is_ssl = self._data.get(CONF_SSL)

            result = await _valid_login(self.hass, host, port, is_ssl, username, password)
            errors = result.get("errors")

            if errors is None:
                return self.async_create_entry(title="", data=self.options)

        options = {
            CONF_USERNAME: self.get_value(CONF_USERNAME, ""),
            CONF_PASSWORD: self.get_value(CONF_PASSWORD, ""),
            CONF_EXCLUDE_SYSTEM_CAMERA: self.get_value(CONF_EXCLUDE_SYSTEM_CAMERA, False)
        }

        username = options.get(CONF_USERNAME, "")
        password = options.get(CONF_PASSWORD, "")

        if len(password) > 0:
            password_manager = PasswordManager(self.hass)
            password = password_manager.decrypt(password)

            options[CONF_PASSWORD] = password

        has_credentials = len(username) > 0 or len(password) > 0

        if has_credentials:
            options[CONF_CLEAR_CREDENTIALS] = False

        fields = {}
        for option in options:
            current_value = options[option]
            obj_type = str
            if option in [CONF_EXCLUDE_SYSTEM_CAMERA, CONF_CLEAR_CREDENTIALS]:
                obj_type = bool

            fields[vol.Optional(option, default=current_value)] = obj_type

        return self.async_show_form(
            step_id="blue_iris_additional_settings",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                CONF_HOST: self._data.get(CONF_HOST)
            }
        )
