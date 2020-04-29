from homeassistant.config_entries import ConfigEntry

from ..helpers.const import *
from ..models.config_data import ConfigData
from .password_manager import PasswordManager


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
        result.port = data.get(CONF_PORT, DEFAULT_PORT)
        result.ssl = data.get(CONF_SSL, False)

        result.username = self._get_config_data_item(CONF_USERNAME, options, data)
        result.password = self._get_config_data_item(CONF_PASSWORD, options, data)

        if len(result.password) > 0:
            result.password_clear_text = self.password_manager.decrypt(result.password)

        result.log_level = options.get(CONF_LOG_LEVEL, LOG_LEVEL_DEFAULT)

        result.allowed_audio_sensor = self._get_allowed_option(
            CONF_ALLOWED_AUDIO_SENSOR, options
        )
        result.allowed_connectivity_sensor = self._get_allowed_option(
            CONF_ALLOWED_CONNECTIVITY_SENSOR, options
        )
        result.allowed_camera = self._get_allowed_option(CONF_ALLOWED_CAMERA, options)
        result.allowed_motion_sensor = self._get_allowed_option(
            CONF_ALLOWED_MOTION_SENSOR, options
        )
        result.allowed_profile = self._get_allowed_option(CONF_ALLOWED_PROFILE, options)

        self.config_entry = config_entry
        self.data = result

    def is_supports_audio_sensor(self, camera):
        audio_support = camera.get("audio", False)
        supports_sensors = self.is_supports_sensors(camera)

        is_supports_audio_sensor = audio_support and supports_sensors

        return is_supports_audio_sensor

    def is_allowed_audio_sensor(self, camera):
        camera_id = camera.get("optionValue")

        allowed_audio_sensor = self.data.allowed_audio_sensor

        is_supported = self.is_supports_audio_sensor(camera)
        is_allowed = allowed_audio_sensor is None or camera_id in allowed_audio_sensor

        result = is_supported and is_allowed

        return result

    def is_allowed_motion_sensor(self, camera):
        camera_id = camera.get("optionValue")

        allowed_motion_sensor = self.data.allowed_motion_sensor

        is_supported = self.is_supports_sensors(camera)
        is_allowed = allowed_motion_sensor is None or camera_id in allowed_motion_sensor

        result = is_supported and is_allowed

        return result

    def is_allowed_connectivity_sensor(self, camera):
        camera_id = camera.get("optionValue")

        allowed_connectivity_sensor = self.data.allowed_connectivity_sensor

        is_supported = self.is_supports_sensors(camera)
        is_allowed = (
            allowed_connectivity_sensor is None
            or camera_id in allowed_connectivity_sensor
        )

        result = is_supported and is_allowed

        return result

    @staticmethod
    def is_supports_sensors(camera):
        camera_id = camera.get("optionValue")

        is_system = camera_id in SYSTEM_CAMERA_ID

        is_supports_sensors = not is_system

        return is_supports_sensors

    @staticmethod
    def _get_allowed_option(key, options):
        allowed_audio_sensor = None
        if key in options:
            allowed_audio_sensor = options.get(key, [])

        return allowed_audio_sensor

    @staticmethod
    def _get_config_data_item(key, options, data):
        data_result = data.get(key, "")

        result = options.get(key, data_result)

        return result
