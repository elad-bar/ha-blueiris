import logging

from homeassistant.const import (CONF_ROOM, CONF_NAME, CONF_ID)
from homeassistant.components.camera.generic import (CONF_STREAM_SOURCE, CONF_STILL_IMAGE_URL)

from .const import *
from .blue_iris_api import BlueIrisApi

_LOGGER = logging.getLogger(__name__)


class BlueIrisData:
    """The Class for handling the data retrieval."""

    def __init__(self, host, port, cameras, mqtt, username, password, ssl, exclude, profiles):
        """Initialize the data object."""
        self._was_initialized = False

        self._configuration_errors = None
        self._configurations = {
                CONF_CAMERAS: {},
                CONF_PROFILE: {}
            }

        self._is_armed = False
        self._is_arming_allowed = False
        self._profile_armed = None
        self._profile_unarmed = None
        self._api = None
        self._stream_url = None
        self._image_url = None
        self._mqtt_watchdog = None
        self._mqtt_motion = None
        self._credentials = None
        self._base_url = None

        self.set_blue_iris_urls(host, port, ssl, username, password)

        self.set_mqtt(mqtt)
        self.set_profiles(profiles)

        self.set_camera_list(cameras, exclude)

        if self._is_arming_allowed:
            self._api = BlueIrisApi(self.base_url, username, password)

    @property
    def base_url(self):
        return self._base_url

    def get_configuration_errors(self):
        return self._configuration_errors

    def log_warn(self, message):
        if self._configuration_errors is None:
            self._configuration_errors = []

        self._configuration_errors.append(f'WARN - {message}')
        _LOGGER.warning(message)

    def log_error(self, message):
        if self._configuration_errors is None:
            self._configuration_errors = []

        self._configuration_errors.append(f'ERROR - {message}')
        _LOGGER.error(message)

    def set_mqtt(self, config):
        if config is not None:
            missing_placeholder = f'Missing {CAMERA_ID_PLACEHOLDER} placeholder'

            self._mqtt_watchdog = config.get(CONF_MQTT_WATCHDOG, '')
            self._mqtt_motion = config.get(CONF_MQTT_MOTION, '')

            if CAMERA_ID_PLACEHOLDER not in self._mqtt_watchdog:
                self._mqtt_watchdog = None
                # self.log_warn(f'Invalid {CONF_MQTT_WATCHDOG} MQTT topic definition, {missing_placeholder}')

            if CAMERA_ID_PLACEHOLDER not in self._mqtt_motion:
                self._mqtt_motion = None
                # self.log_warn(f'Invalid {CONF_MQTT_MOTION} MQTT topic definition, {missing_placeholder}')

    def set_camera_list(self, cameras, exclude):
        for system_camera in SYSTEM_CAMERA_CONFIG:
            if system_camera in cameras:
                self.log_warn(f'System camera cannot be added, please remove camera: {system_camera}')

            if exclude is None or system_camera not in exclude:
                camera = {
                    CONF_NAME: system_camera,
                    CONF_ID: SYSTEM_CAMERA_CONFIG[system_camera]
                }

                cameras.append(camera)

        for camera in cameras:
            self.add_camera(camera)

    def set_profiles(self, profiles):
        if profiles is not None:
            if self._credentials is None:
                self.log_error('Cannot set profile of BlueIris without administrator credentials')
                return

            self._profile_armed = profiles.get(CONF_PROFILE_ARMED)
            self._profile_unarmed = profiles.get(CONF_PROFILE_UNARMED)

            self._is_arming_allowed = bool(self._profile_armed is not None and self._profile_unarmed is not None)

    def set_blue_iris_urls(self, host, port, ssl, username, password):
        self._base_url = f'{PROTOCOLS[ssl]}://{host}:{port}'

        if username is not None and password is not None:
            self._credentials = f'&username={username}&password={password}'

        self._image_url = f'{self._base_url}/image/[camera_id]?q=100&s=100'
        self._stream_url = f'{self._base_url}/h264/[camera_id]/temp.m3u8'

        self._image_url = f'{self._image_url}&{self._credentials}'

    def add_camera(self, camera):
        camera_mqtt_watchdog = None
        camera_mqtt_motion = None

        camera_id = camera.get(CONF_ID)
        camera_name = camera.get(CONF_NAME, camera_id)
        camera_room = camera.get(CONF_ROOM)

        if camera_name not in SYSTEM_CAMERA_CONFIG:
            if self._mqtt_watchdog is not None:
                camera_mqtt_watchdog = self._mqtt_watchdog.replace(CAMERA_ID_PLACEHOLDER, camera_id)

            if self._mqtt_motion is not None:
                camera_mqtt_motion = self._mqtt_motion.replace(CAMERA_ID_PLACEHOLDER, camera_id)

        camera_still_url = self._image_url.replace(CAMERA_ID_PLACEHOLDER, camera_id)
        camera_source = self._stream_url.replace(CAMERA_ID_PLACEHOLDER, camera_id)

        camera_details = {
            CONF_NAME: f'BI {camera_name}',
            CONF_ROOM: camera_room,
            CONF_STILL_IMAGE_URL: camera_still_url,
            CONF_STREAM_SOURCE: camera_source,
            CONF_MQTT_WATCHDOG: camera_mqtt_watchdog,
            CONF_MQTT_MOTION: camera_mqtt_motion,
        }

        _LOGGER.debug(f'BlueIris camera configuration loaded, details: {camera_details}')
        self._configurations[CONF_CAMERAS][camera_id] = camera_details

    def get_all_cameras(self):
        return self._configurations[CONF_CAMERAS]

    def is_blue_iris_armed(self):
        return self._is_armed

    def update_blue_iris_profile(self, arm):
        if not self._is_arming_allowed:
            _LOGGER.warning('Configuration not support Arming BlueIris')
            return

        profile = self._profile_unarmed

        if arm:
            profile = self._profile_armed

        self._api.update_blue_iris_profile(profile)

        self._is_armed = arm

    def get_arm_state(self):
        if not self._is_arming_allowed:
            _LOGGER.warning('Configuration not support get Arming State from BlueIris')
            return

        data = self._api.get_data()
        state = f'profile={self._profile_armed}' in data

        return state

    def update(self):
        _LOGGER.debug("update - Start")

        if self._is_arming_allowed:
            self._is_armed = self.get_arm_state()

        _LOGGER.debug("update - Completed")
