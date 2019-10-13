import logging

from homeassistant.const import (CONF_ROOM, CONF_NAME, CONF_ID, CONF_USERNAME,
                                 CONF_PASSWORD, CONF_AUTHENTICATION)
from homeassistant.components.generic.camera import (CONF_STREAM_SOURCE,
                                                     CONF_STILL_IMAGE_URL)


from .const import *
from .blue_iris_api import BlueIrisApi

_LOGGER = logging.getLogger(__name__)


class BlueIrisData:
    """The Class for handling the data retrieval."""

    def __init__(self, host, port, cameras, username, password, ssl, exclude,
                 profiles, scan_interval, cv_template):
        """Initialize the data object."""
        self._was_initialized = False
        self._scan_interval = scan_interval

        self._configuration_errors = None
        self._configurations = {CONF_CAMERAS: {}, CONF_PROFILE: {}}

        self._is_armed = False
        self._is_arming_allowed = False
        self._profile_armed = None
        self._profile_unarmed = None
        self._api = None
        self._stream_url = None
        self._image_url = None
        self._credentials = None
        self._base_url = None
        self._cast_url = None
        self._cv_template = cv_template
        self._username = username
        self._password = password

        self.set_blue_iris_urls(host, port, ssl)

        self.set_profiles(profiles)

        self.set_camera_list(cameras, exclude)

        if self._is_arming_allowed:
            self._api = BlueIrisApi(self.base_url, username, password)

    @property
    def scan_interval(self):
        return self._scan_interval

    @property
    def cast_url(self):
        return self._cast_url

    @property
    def base_url(self):
        return self._base_url

    def get_configuration_errors(self):
        return self._configuration_errors

    def log_warn(self, message):
        if self._configuration_errors is None:
            self._configuration_errors = []

        self._configuration_errors.append(f"WARN - {message}")
        _LOGGER.warning(message)

    def log_error(self, message):
        if self._configuration_errors is None:
            self._configuration_errors = []

        self._configuration_errors.append(f"ERROR - {message}")
        _LOGGER.error(message)

    def set_camera_list(self, cameras, exclude):
        for system_camera in SYSTEM_CAMERA_CONFIG:
            if system_camera in cameras:
                self.log_warn(f"System camera cannot be added, " 
                              f"please remove camera: {system_camera}")

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
                self.log_error("Profile state requires admin credentials")
                return

            self._profile_armed = profiles.get(CONF_PROFILE_ARMED)
            self._profile_unarmed = profiles.get(CONF_PROFILE_UNARMED)

            self._is_arming_allowed = bool(
                self._profile_armed is not None and
                self._profile_unarmed is not None)

    def set_blue_iris_urls(self, host, port, ssl):
        self._credentials = ''
        cast_credentials = ""
        if self._username is not None and self._password is not None:
            self._credentials = f'{self._username}:{self._password}@'
            cast_credentials = f"?user={self._username}&pw={self._password}"

        self._base_url = f'{PROTOCOLS[ssl]}://{host}:{port}'
        self._cast_url = f'{PROTOCOLS[ssl]}://{host}:{port}/mjpg/[CAM_ID]/video.mjpg{cast_credentials}'

        self._image_url = f'{self._base_url}/image/[camera_id]?q=100&s=100'
        self._stream_url = f'{self._base_url}/h264/[camera_id]/temp.m3u8'

    def add_camera(self, camera):
        camera_id = camera.get(CONF_ID)

        camera_details = {
            CONF_ID: camera_id,
            CONF_NAME: camera.get(CONF_NAME, camera_id),
            CONF_ROOM: camera.get(CONF_ROOM),
            CONF_STILL_IMAGE_URL: self._cv_template(self._image_url.replace(
                CAMERA_ID_PLACEHOLDER, camera_id)),
            CONF_STREAM_SOURCE: self._stream_url.replace(
                CAMERA_ID_PLACEHOLDER, camera_id),
            CONF_USERNAME: self._username,
            CONF_PASSWORD: self._password
        }

        _LOGGER.debug(f"Blue Iris camera loaded, details: {camera_details}")

        self._configurations[CONF_CAMERAS][camera_id] = camera_details

    def get_all_cameras(self):
        return self._configurations[CONF_CAMERAS]

    def is_blue_iris_armed(self):
        return self._is_armed

    def update_blue_iris_profile(self, arm):
        if not self._is_arming_allowed:
            _LOGGER.warning("No support for set arm state")
            return

        profile = self._profile_unarmed

        if arm:
            profile = self._profile_armed

        self._api.update_blue_iris_profile(profile)

        self._is_armed = arm

    def get_arm_state(self):
        if not self._is_arming_allowed:
            _LOGGER.warning("No support to get armed state")
            return

        data = self._api.get_data()
        state = False

        if data is None:
            _LOGGER.warning("Failed to get profile")
        else:
            state = f'profile={self._profile_armed}' in data

        return state

    def update(self):
        _LOGGER.debug("update - Start")

        if self._is_arming_allowed:
            self._is_armed = self.get_arm_state()

        _LOGGER.debug("update - Completed")
