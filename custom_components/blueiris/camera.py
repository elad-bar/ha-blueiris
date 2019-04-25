"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/camera.blueiris/
"""
import asyncio
import logging

import aiohttp
import async_timeout
import requests
from requests.auth import HTTPDigestAuth

from homeassistant.const import (
    CONF_NAME, CONF_USERNAME, CONF_PASSWORD, CONF_AUTHENTICATION,
    HTTP_BASIC_AUTHENTICATION, HTTP_DIGEST_AUTHENTICATION, CONF_VERIFY_SSL)
from homeassistant.components.camera import (
    DEFAULT_CONTENT_TYPE, SUPPORT_STREAM, Camera)
from homeassistant.components.generic.camera import (
    CONF_LIMIT_REFETCH_TO_URL_CHANGE, CONF_FRAMERATE, CONF_CONTENT_TYPE,
    CONF_STREAM_SOURCE, CONF_STILL_IMAGE_URL)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util.async_ import run_coroutine_threadsafe

from .const import *

DEPENDENCIES = [DOMAIN]

_LOGGER = logging.getLogger(__name__)


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_entities,
                         discovery_info=None):
    """Set up a Blue Iris Camera."""
    bi_data = hass.data.get(DATA_BLUEIRIS)

    if not bi_data:
        return

    cameras = bi_data.get_all_cameras()

    bi_camera_list = []
    for camera_id in cameras:
        camera = cameras[camera_id]
        _LOGGER.debug(f'Processing new camera: {camera}')

        device_info = {
            CONF_NAME: camera[CONF_NAME],
            CONF_STILL_IMAGE_URL: camera[CONF_STILL_IMAGE_URL],
            CONF_STREAM_SOURCE: camera[CONF_STREAM_SOURCE],
            CONF_LIMIT_REFETCH_TO_URL_CHANGE: False,
            CONF_FRAMERATE: 2,
            CONF_VERIFY_SSL: False,
            CONF_CONTENT_TYPE: DEFAULT_CONTENT_TYPE
        }

        bi_camera = BlueIrisCamera(hass, device_info)
        bi_camera_list.append(bi_camera)

        _LOGGER.debug(f'Camera created: {bi_camera}')

    async_add_entities(bi_camera_list, True)


class BlueIrisCamera(Camera):
    """A generic implementation of an IP camera."""

    def turn_off(self):
        pass

    def turn_on(self):
        pass

    def enable_motion_detection(self):
        pass

    def disable_motion_detection(self):
        pass

    def __init__(self, hass, device_info):
        """Initialize a generic camera."""
        super().__init__()

        self.hass = hass
        self._authentication = device_info.get(CONF_AUTHENTICATION)
        self._name = device_info.get(CONF_NAME)
        self._still_image_url = device_info[CONF_STILL_IMAGE_URL]
        self._stream_source = device_info[CONF_STREAM_SOURCE]
        self._still_image_url.hass = hass
        self._limit_refetch = device_info[CONF_LIMIT_REFETCH_TO_URL_CHANGE]
        self._frame_interval = 1 / device_info[CONF_FRAMERATE]
        self._supported_features = SUPPORT_STREAM if self._stream_source else 0
        self.content_type = device_info[CONF_CONTENT_TYPE]
        self.verify_ssl = device_info[CONF_VERIFY_SSL]

        username = None
        password = None

        if username and password:
            if self._authentication == HTTP_DIGEST_AUTHENTICATION:
                self._auth = HTTPDigestAuth(username, password)
            else:
                self._auth = aiohttp.BasicAuth(username, password=password)
        else:
            self._auth = None

        self._last_url = None
        self._last_image = None

    @property
    def supported_features(self):
        """Return supported features for this camera."""
        return self._supported_features

    @property
    def frame_interval(self):
        """Return the interval between frames of the MJPEG stream."""
        return self._frame_interval

    def camera_image(self):
        """Return bytes of camera image."""
        return run_coroutine_threadsafe(
            self.async_camera_image(), self.hass.loop).result()

    async def async_camera_image(self):
        """Return a still image response from the camera."""
        if self._still_image_url == self._last_url and self._limit_refetch:
            return self._last_image

        try:
            session = async_get_clientsession(
                self.hass, verify_ssl=self.verify_ssl)

            with async_timeout.timeout(
                    IMAGE_TIMEOUT.seconds, loop=self.hass.loop):
                response = await session.get(
                    self._still_image_url, auth=self._auth)

                self._last_image = await response.read()

            self._last_url = self._still_image_url

        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout getting image from: {self._name}")

        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error getting new camera image: {err}")

        return self._last_image

    @property
    def name(self):
        """Return the name of this device."""
        return self._name

    @property
    def stream_source(self):
        """Return the source of the stream."""
        return self._stream_source
