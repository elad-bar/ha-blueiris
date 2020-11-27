import logging

from homeassistant.config_entries import ConfigEntry

from ..helpers.const import *
from ..models.camera_data import CameraData
from ..models.config_data import ConfigData
from .password_manager import PasswordManager

_LOGGER = logging.getLogger(__name__)


class ConfigManager:
    data: ConfigData
    config_entry: ConfigEntry
    password_manager: PasswordManager

    def __init__(self, password_manager: PasswordManager):
        self.password_manager = password_manager

    async def update(self, config_entry: ConfigEntry):
        data = config_entry.data
        options = config_entry.options

        result: ConfigData = await self.get_basic_data(data)

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
        result.allowed_dio_sensor = self._get_allowed_option(
            CONF_ALLOWED_DIO_SENSOR, options
        )
        result.allowed_external_sensor = self._get_allowed_option(
            CONF_ALLOWED_EXTERNAL_SENSOR, options
        )
        result.allowed_profile = self._get_allowed_option(CONF_ALLOWED_PROFILE, options)

        result.allowed_schedule = self._get_allowed_option(CONF_ALLOWED_SCHEDULE, options)

        result.stream_type = options.get(CONF_STREAM_TYPE, DEFAULT_STREAM_TYPE)

        result.support_stream = options.get(CONF_SUPPORT_STREAM, False)

        self.config_entry = config_entry
        self.data = result

    async def get_basic_data(self, data):
        result = ConfigData()

        if data is not None:
            result.host = data.get(CONF_HOST)
            result.port = data.get(CONF_PORT, DEFAULT_PORT)
            result.ssl = data.get(CONF_SSL, False)

            result.username = data.get(CONF_USERNAME)
            result.password = data.get(CONF_PASSWORD)

            if result.password is not None and len(result.password) > 0:
                result.password_clear_text = await self.password_manager.decrypt(
                    result.password
                )
            else:
                result.password_clear_text = result.password

        return result

    def get_allowed_sensor_state(self, sensor_type):
        sensor_states = {
            SENSOR_CONNECTIVITY_NAME: self.data.allowed_connectivity_sensor,
            SENSOR_MOTION_NAME: self.data.allowed_motion_sensor,
            SENSOR_EXTERNAL_NAME: self.data.allowed_external_sensor,
            SENSOR_DIO_NAME: self.data.allowed_dio_sensor,
            SENSOR_AUDIO_NAME: self.data.allowed_audio_sensor,
        }

        sensor_state = sensor_states[sensor_type]

        return sensor_state

    def is_allowed_sensor(self, camera: CameraData, sensor_type):
        allowed_camera = self.get_allowed_sensor_state(sensor_type)

        is_supported = not camera.is_system

        if is_supported and sensor_type == SENSOR_AUDIO_NAME:
            is_supported = camera.has_audio

        is_allowed = allowed_camera is None or camera.id in allowed_camera

        result = is_supported and is_allowed

        return result

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
