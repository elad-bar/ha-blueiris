"""Config flow to configure BlueIris."""
import logging

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant

from .managers.configuration_manager import ConfigManager
from .managers.password_manager import PasswordManager
from .api.blue_iris_api import BlueIrisApi
from .helpers.const import *
from .models.config_data import ConfigData

_LOGGER = logging.getLogger(__name__)


class BlueIrisConfigFlow:
    config_manager: ConfigManager
    password_manager: PasswordManager
    is_initialized: bool = False

    def initialize(self, hass: HomeAssistant):
        if not self.is_initialized:
            self.password_manager = PasswordManager(hass)
            self.config_manager = ConfigManager(self.password_manager)

            self.is_initialized = True

    def update_config_data(self, data: dict, options: dict = None):
        entry = ConfigEntry(0, "", "", data, "", "", {}, options=options)

        self.config_manager.update(entry)

    async def valid_login(self, hass):
        errors = None

        config_data = self.config_manager.data

        api = BlueIrisApi(hass, self.config_manager)
        await api.initialize()

        if not api.is_logged_in:
            _LOGGER.warning(f"Failed to access BlueIris Server ({config_data.host})")
            errors = {
                "base": "invalid_server_details"
            }
        else:
            has_credentials = config_data.has_credentials

            if has_credentials and not api.data.get("admin", False):
                _LOGGER.warning(f"Failed to login BlueIris ({config_data.host}) due to invalid credentials")
                errors = {
                    "base": "invalid_admin_credentials"
                }

        return {
            "logged-in": errors is None,
            "errors": errors
        }


@config_entries.HANDLERS.register(DOMAIN)
class BlueIrisFlowHandler(config_entries.ConfigFlow, BlueIrisConfigFlow):
    """Handle a BlueIris config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        options_handler = BlueIrisOptionsFlowHandler(config_entry)

        return options_handler

    async def async_step_user(self, user_input=None):
        """Handle a flow start."""
        _LOGGER.debug(f"Starting async_step_user of {DOMAIN}")

        if self._async_current_entries():
            return self.async_abort(reason="one_instance_only")

        errors = None

        self.initialize(self.hass)

        if user_input is not None:
            if CONF_PASSWORD in user_input:
                password = user_input[CONF_PASSWORD]
                user_input[CONF_PASSWORD] = self.password_manager.encrypt(password)

            self.update_config_data(user_input)

            result = await self.valid_login(self.hass)
            errors = result.get("errors")

            if errors is None:
                return self.async_create_entry(title=self.config_manager.data.host, data=user_input)

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


class BlueIrisOptionsFlowHandler(config_entries.OptionsFlow, BlueIrisConfigFlow):
    """Handle BlueIris options."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize BlueIris options flow."""
        super().__init__()

        self.options = {}
        self._data = {}

        for key in config_entry.options.keys():
            self.options[key] = config_entry.options[key]

        for key in config_entry.data.keys():
            self._data[key] = config_entry.data[key]

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

        self.initialize(self.hass)

        if user_input is not None:
            clear_credentials = user_input.get(CONF_CLEAR_CREDENTIALS, False)

            if clear_credentials:
                del user_input[CONF_USERNAME]
                del user_input[CONF_PASSWORD]
            else:
                if CONF_PASSWORD in user_input:
                    password = user_input[CONF_PASSWORD]
                    user_input[CONF_PASSWORD] = self.password_manager.encrypt(password)

            self.update_config_data(self._data, user_input)

            result = await self.valid_login(self.hass)
            errors = result.get("errors")

            if errors is None:
                return self.async_create_entry(title="", data=user_input)

        self.update_config_data(self._data, self.options)
        config_data = self.config_manager.data

        options = {
            CONF_USERNAME: config_data.username,
            CONF_PASSWORD: config_data.password_clear_text,
            CONF_EXCLUDE_SYSTEM_CAMERA: config_data.exclude_system_camera
        }

        fields = {}
        for option in options:
            current_value = options[option]
            obj_type = str
            if option in [CONF_EXCLUDE_SYSTEM_CAMERA, CONF_CLEAR_CREDENTIALS]:
                obj_type = bool

            fields[vol.Optional(option, default=current_value)] = obj_type

        fields[vol.Optional(CONF_CLEAR_CREDENTIALS, default=False)] = bool

        return self.async_show_form(
            step_id="blue_iris_additional_settings",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                CONF_HOST: config_data.host
            }
        )
