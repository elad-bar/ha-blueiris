from homeassistant.config_entries import ConfigEntry

from .password_manager import PasswordManager
from ..helpers.const import *
from ..models.config_data import ConfigData


class ConfigManager:
    data: ConfigData
    config_entry: ConfigEntry
    password_manager: PasswordManager

    def __init__(self, password_manager: PasswordManager):
        self.password_manager = password_manager

    def update(self, config_entry: ConfigEntry):
        data = config_entry.data
        options = config_entry.options

        result = ConfigData()

        result.host = data.get(CONF_HOST)
        result.port = data.get(CONF_PORT)
        result.ssl = data.get(CONF_SSL, False)

        result.username = self._get_config_data_item(CONF_USERNAME, options, data)
        result.password = self._get_config_data_item(CONF_PASSWORD, options, data)

        if len(result.password) > 0:
            result.password_clear_text = self.password_manager.decrypt(result.password)

        result.exclude_system_camera = options.get(CONF_EXCLUDE_SYSTEM_CAMERA, False)

        self.config_entry = config_entry
        self.data = result

    @staticmethod
    def _get_config_data_item(key, options, data):
        data_result = data.get(key, "")

        result = options.get(key, data_result)

        return result
