"""
This component provides support for Blue Iris.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/blueiris/
"""
import logging
import urllib.error
import urllib.request
from datetime import timedelta

import requests
import voluptuous as vol
from homeassistant.components.camera.mjpeg import (CONF_STILL_IMAGE_URL, CONF_MJPEG_URL)
from homeassistant.const import (
    CONF_ROOM, CONF_EXCLUDE, CONF_NAME, CONF_HOST, CONF_PORT, CONF_PASSWORD,
    CONF_USERNAME, CONF_SSL, CONF_ID, EVENT_HOMEASSISTANT_START)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import track_time_interval
from requests.auth import HTTPBasicAuth

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'blueiris'
DATA_BLUEIRIS = 'data_{}'.format(DOMAIN)
DEFAULT_NAME = 'Blue Iris'
SIGNAL_UPDATE_BLUEIRIS = 'updates_{}'.format(DOMAIN)

ATTR_ADMIN_PROFILE = 'Profile'
ATTR_SYSTEM_CAMERA_ALL_NAME = 'All'
ATTR_SYSTEM_CAMERA_ALL_ID = 'Index'
ATTR_SYSTEM_CAMERA_CYCLE_NAME = 'Cycle'
ATTR_SYSTEM_CAMERA_CYCLE_ID = '@Index'

BLUEIRIS_AUTH_ERROR = 'Authorization required'

SYSTEM_CAMERA_CONFIG = {
    ATTR_SYSTEM_CAMERA_ALL_NAME: ATTR_SYSTEM_CAMERA_ALL_ID,
    ATTR_SYSTEM_CAMERA_CYCLE_NAME: ATTR_SYSTEM_CAMERA_CYCLE_ID
}

CONF_CAMERAS = 'camera'
CONF_MQTT = 'mqtt'
CONF_MQTT_WATCHDOG = 'watchdog'
CONF_MQTT_MOTION = 'motion'

CONF_PROFILE = 'profile'
CONF_PROFILE_ARMED = 'armed'
CONF_PROFILE_UNARMED = 'unarmed'

NOTIFICATION_ID = '{}_notification'.format(DOMAIN)
NOTIFICATION_TITLE = '{} Setup'.format(DEFAULT_NAME)

SCAN_INTERVAL = timedelta(seconds=60)

CAMERA_SCHEMA = vol.Schema({
    vol.Required(CONF_ID): cv.string,
    vol.Optional(CONF_NAME, default=None): cv.string,
    vol.Optional(CONF_ROOM, default=None): cv.string,
})

MQTT_SCHEMA = vol.Schema({
    vol.Optional(CONF_MQTT_WATCHDOG): cv.string,
    vol.Optional(CONF_MQTT_MOTION): cv.string,
})

PROFILE_SCHEMA = vol.Schema({
    vol.Required(CONF_PROFILE_ARMED): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
    vol.Required(CONF_PROFILE_UNARMED): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.string,
        vol.Required(CONF_CAMERAS):
            vol.All(cv.ensure_list, [vol.Any(CAMERA_SCHEMA)]),
        vol.Optional(CONF_EXCLUDE):
            vol.All(cv.ensure_list, [vol.In(SYSTEM_CAMERA_CONFIG)]),
        vol.Optional(CONF_PROFILE): PROFILE_SCHEMA,
        vol.Optional(CONF_MQTT): MQTT_SCHEMA,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SSL, default=False): cv.boolean,
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up a Blue Iris component."""
    try:
        conf = config[DOMAIN]
        scan_interval = SCAN_INTERVAL
        host = conf.get(CONF_HOST)
        port = conf.get(CONF_PORT)
        cameras = conf.get(CONF_CAMERAS)
        exclude = conf.get(CONF_EXCLUDE)
        mqtt = conf.get(CONF_MQTT)
        username = conf.get(CONF_USERNAME)
        password = conf.get(CONF_PASSWORD)
        ssl = conf.get(CONF_SSL)
        profile = conf.get(CONF_PROFILE)

        bi_data = BlueIrisData(hass, scan_interval, host, port, cameras, mqtt, username, password, ssl,
                               exclude, profile)

        hass.data[DATA_BLUEIRIS] = bi_data

        configuration_errors = bi_data.get_configuration_errors()

        if configuration_errors is not None:
            error_message = '<b>Errors while loading configuration:</b><br /> {}'.format(
                '<br /> - '.join(configuration_errors))

            hass.components.persistent_notification.create(
                error_message,
                title=NOTIFICATION_TITLE,
                notification_id=NOTIFICATION_ID)

            return False

        return True
    except Exception as ex:
        error_message = '<b>Errors while loading configuration:</b><br />Exception: {}'.format(str(ex))

        _LOGGER.error(error_message)

        hass.components.persistent_notification.create(
            error_message,
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID)

        return False


class BlueIrisData:
    """The Class for handling the data retrieval."""

    def __init__(self, hass, scan_interval, host, port, cameras, mqtt, username, password, ssl, exclude, profile):
        """Initialize the data object."""
        configuration_args = 'host: {}, port: {}, cameras: {}, mqtt: {}, username: {}, password: {}, ssl: {}'.format(
                host, port, cameras, mqtt, username, password, ssl)

        _LOGGER.debug(
            'BlueIrisData initialization with following configuration: {}'.format(configuration_args))

        self._host = host
        self._port = port
        self._ssl = ssl
        self._username = username
        self._password = password
        self._cameras = cameras
        self._mqtt = mqtt
        self._exclude = exclude
        self._profile = profile

        self._hass = hass
        self._was_initialized = False

        self._configuration_errors = None
        self._cameraConfigurations = None

        self._is_arming_allowed = False
        self._admin_url = None
        self._profile_armed = None
        self._profile_unarmed = None

        self._is_armed = False

        self.build_configuration()

        if self._is_arming_allowed and CONF_PROFILE in self._cameraConfigurations:
            profile_details = self._cameraConfigurations[CONF_PROFILE]

            self._admin_url = profile_details[ATTR_ADMIN_PROFILE]
            self._profile_armed = profile_details[CONF_PROFILE_ARMED]
            self._profile_unarmed = profile_details[CONF_PROFILE_UNARMED]

        def bi_refresh(event_time):
            """Call BlueIris to refresh information."""
            _LOGGER.debug('Updating BlueIris component'.format(event_time))
            self.update()
            dispatcher_send(hass, SIGNAL_UPDATE_BLUEIRIS)

        self._bi_refresh = bi_refresh

        # register service
        hass.services.register(DOMAIN, 'update', bi_refresh)

        track_time_interval(hass, bi_refresh, scan_interval)

        hass.bus.listen_once(EVENT_HOMEASSISTANT_START, bi_refresh)

    def get_configuration_errors(self):
        return self._configuration_errors

    def log_warn(self, message):
        if self._configuration_errors is None:
            self._configuration_errors = []

        self._configuration_errors.append('WARN - {}'.format(message))
        _LOGGER.warning(message)

    def log_error(self, message):
        if self._configuration_errors is None:
            self._configuration_errors = []

        self._configuration_errors.append('ERROR - {}'.format(message))
        _LOGGER.error(message)

    def build_configuration(self):
        try:
            configuration = {
                CONF_CAMERAS: {},
                CONF_PROFILE: {}
            }
            mqtt_watchdog = None
            mqtt_motion = None

            camera_id_placeholder = '[camera_id]'

            if self._mqtt is not None:
                if CONF_MQTT_WATCHDOG in self._mqtt:
                    mqtt_watchdog = self._mqtt[CONF_MQTT_WATCHDOG]

                    if mqtt_watchdog is not None and mqtt_watchdog != '' and camera_id_placeholder not in mqtt_watchdog:
                        self.log_warn('Invalid watchdog MQTT topic definition, missing {} placeholder'.format(
                            camera_id_placeholder))

                if CONF_MQTT_MOTION in self._mqtt:
                    mqtt_motion = self._mqtt[CONF_MQTT_MOTION]

                    if mqtt_motion is not None and mqtt_motion != '' and camera_id_placeholder not in mqtt_motion:
                        self.log_warn('Invalid motion MQTT topic definition, missing {} placeholder'.format(
                            camera_id_placeholder))

            for system_camera in SYSTEM_CAMERA_CONFIG:
                if system_camera in self._cameras:
                    self.log_warn("System camera cannot be added, please remove camera: {}".format(system_camera))

                if self._exclude is None or system_camera not in self._exclude:
                    camera = {
                        CONF_NAME: system_camera,
                        CONF_ID: SYSTEM_CAMERA_CONFIG[system_camera]
                    }

                    self._cameras.append(camera)

            protocol = 'http'
            if self._ssl:
                protocol = 'https'

            if self._profile is not None and CONF_PROFILE_ARMED in self._profile and \
                    CONF_PROFILE_UNARMED in self._profile:

                profile_armed = self._profile[CONF_PROFILE_ARMED]
                profile_unarmed = self._profile[CONF_PROFILE_UNARMED]

                if self._username is None or self._password is None:
                    self.log_error('Cannot set profile of BlueIris without administrator credentails')
                    return

                self._is_arming_allowed = True

                profile_settings = {
                    ATTR_ADMIN_PROFILE: '{}://{}:{}/admin'.format(protocol, self._host, self._port),
                    CONF_PROFILE_ARMED: profile_armed,
                    CONF_PROFILE_UNARMED: profile_unarmed
                }

                configuration[CONF_PROFILE] = profile_settings

            url = '{}://{}:{}/[format]/[camera_id][query_string]'.format(protocol, self._host, self._port)
            image_url = url.replace('[format]', 'image').replace('[query_string]', '?q=80&s=80')
            mjpeg_url = url.replace('[format]', 'mjpg').replace('[query_string]', '/video.mjpg?q=80&s=80')

            if self._username is not None and self._username != '':
                credentials = 'username={}&password={}'.format(self._username, self._password)

                image_url = '{}&{}'.format(image_url, credentials)
                mjpeg_url = '{}?{}'.format(mjpeg_url, credentials)

            for camera in self._cameras:
                camera_id = camera[CONF_ID]
                camera_room = None
                camera_mqtt_watchdog = None
                camera_mqtt_motion = None

                if CONF_NAME in camera:
                    camera_name = camera[CONF_NAME]
                else:
                    camera_name = camera_id

                if CONF_ROOM in camera:
                    camera_room = camera[CONF_ROOM]

                if camera_name not in SYSTEM_CAMERA_CONFIG:
                    if mqtt_watchdog is not None:
                        camera_mqtt_watchdog = mqtt_watchdog.replace(camera_id_placeholder, camera_id)

                    if mqtt_motion is not None:
                        camera_mqtt_motion = mqtt_motion.replace(camera_id_placeholder, camera_id)

                camera_details = {
                    CONF_NAME: 'BI {}'.format(camera_name),
                    CONF_ROOM: camera_room,
                    CONF_STILL_IMAGE_URL: image_url.replace(camera_id_placeholder, camera_id),
                    CONF_MJPEG_URL: mjpeg_url.replace(camera_id_placeholder, camera_id),
                    CONF_MQTT_WATCHDOG: camera_mqtt_watchdog,
                    CONF_MQTT_MOTION: camera_mqtt_motion,
                }

                _LOGGER.debug('BlueIris camera configuration loaded, details: {}'.format(camera_details))
                configuration[CONF_CAMERAS][camera_id] = camera_details

            _LOGGER.debug('BlueIris configuration loaded, details: {}'.format(configuration))

            self._cameraConfigurations = configuration
        except Exception as ex:
            self.log_error("buildConfiguration failed due to the following exception: {}".format(str(ex)))

    def get_all_cameras(self):
        return self._cameraConfigurations[CONF_CAMERAS]

    def is_blue_iris_armed(self):
        return self._is_armed

    def update_blue_iris_profile(self, arm):
        if not self._is_arming_allowed:
            _LOGGER.warning('Configuration not support Arming BlueIris')
            return

        profile = self._profile_unarmed

        if arm:
            profile = self._profile_armed

        request_data = '?profile={}&lock=2'.format(profile)

        self.call_blue_iris_admin(request_data)

        self._is_armed = arm

    def get_arm_state(self):
        if not self._is_arming_allowed:
            _LOGGER.warning('Configuration not support get Arming State from BlueIris')
            return

        response = self.call_blue_iris_admin(None)
        state = 'profile={}'.format(self._profile_armed) in response

        _LOGGER.debug('Status of BlueIris: {}'.format(response))

        return state

    def call_blue_iris_admin(self, request_data):
        auth = HTTPBasicAuth(self._username, self._password)
        response = None

        try:
            if request_data is None:
                request_data = ''

            url = '{}{}'.format(self._admin_url, request_data)

            _LOGGER.debug("Request to BlueIris sent to: {}".format(url))
            r = requests.get(url, auth=auth, timeout=5)
            response = r.text

            if BLUEIRIS_AUTH_ERROR in response:
                _LOGGER.warning('Username and password are incorrect')

        except urllib.error.HTTPError as e:
            _LOGGER.error("Failed to get response from BlueIris due to HTTP Error: {}".format(str(e)))
        except Exception as ex:
            _LOGGER.error("Failed to get response from BlueIris due to unexpected error: {}".format(str(ex)))

        return response

    def update(self):
        _LOGGER.debug("update - Start")

        if self._is_arming_allowed:
            self._is_armed = self.get_arm_state()

        _LOGGER.debug("update - Completed")
