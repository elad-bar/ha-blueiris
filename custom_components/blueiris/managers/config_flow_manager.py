import logging
from typing import Optional

from homeassistant.config_entries import ConfigEntry

from ..helpers.const import *
from ..api.blue_iris_api import BlueIrisApi

from ..managers.configuration_manager import ConfigManager
from ..managers.password_manager import PasswordManager
from ..models.config_data import ConfigData

_LOGGER = logging.getLogger(__name__)


class ConfigFlowManager:
    config_manager: ConfigManager
    password_manager: PasswordManager
    options: Optional[dict]
    data: Optional[dict]
    config_entry: ConfigEntry

    def __init__(self, config_entry: Optional[ConfigEntry] = None):
        self.config_entry = config_entry

        self.options = None
        self.data = None
        self._pre_config = False

        if config_entry is not None:
            self._pre_config = True

            self.update_data(self.config_entry.data)
            self.update_options(self.config_entry.options)

        self._is_initialized = True
        self._auth_error = False
        self._hass = None

    def initialize(self, hass):
        self._hass = hass

        if not self._pre_config:
            self.options = {}
            self.data = {}

        self.password_manager = PasswordManager(self._hass)
        self.config_manager = ConfigManager(self.password_manager)

        self._update_entry()

    @property
    def config_data(self) -> ConfigData:
        return self.config_manager.data

    def handle_password(self, user_input):
        clear_credentials = user_input.get(CONF_CLEAR_CREDENTIALS, False)

        if clear_credentials:
            del user_input[CONF_USERNAME]
            del user_input[CONF_PASSWORD]
        else:
            if CONF_PASSWORD in user_input:
                password_clear_text = user_input[CONF_PASSWORD]
                password = self.password_manager.encrypt(password_clear_text)

                user_input[CONF_PASSWORD] = password

    def update_options(self, options: dict, update_entry: bool = False):
        if options is not None:
            if update_entry:
                self.handle_password(options)
                
            new_options = {}
            for key in options:
                new_options[key] = options[key]

            self.options = new_options
        else:
            self.options = {}

        if update_entry:
            self._update_entry()

    def update_data(self, data: dict, update_entry: bool = False):
        new_data = None

        if data is not None:
            if update_entry:
                self.handle_password(data)

            new_data = {}
            for key in data:
                new_data[key] = data[key]

        self.data = new_data

        if update_entry:
            self._update_entry()

    def _update_entry(self):
        entry = ConfigEntry(0, "", "", self.data, "", "", {}, options=self.options)

        self.config_manager.update(entry)

    @staticmethod
    def get_default_data():
        fields = {
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT): int,
            vol.Optional(CONF_SSL, default=False): bool,
            vol.Optional(CONF_USERNAME): str,
            vol.Optional(CONF_PASSWORD): str,
        }

        data_schema = vol.Schema(fields)

        return data_schema

    def get_default_options(self):
        config_data = self.config_data

        options = {
            CONF_USERNAME: config_data.username,
            CONF_PASSWORD: config_data.password_clear_text,
            CONF_EXCLUDE_SYSTEM_CAMERA: config_data.exclude_system_camera,
            CONF_CLEAR_CREDENTIALS: False
        }

        fields = {}
        for option in options:
            current_value = options[option]
            obj_type = str
            if option in [CONF_EXCLUDE_SYSTEM_CAMERA, CONF_CLEAR_CREDENTIALS]:
                obj_type = bool

            fields[vol.Optional(option, default=current_value)] = obj_type

        data_schema = vol.Schema(fields)

        return data_schema

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
