"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/camera.blueiris/
"""
import logging

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import (CONF_USERNAME, CONF_VERIFY_SSL, CONF_NAME,
                                 CONF_PASSWORD, CONF_AUTHENTICATION)
from homeassistant.components.camera import (
    DEFAULT_CONTENT_TYPE)
from homeassistant.components.generic.camera import (
    CONF_LIMIT_REFETCH_TO_URL_CHANGE, CONF_FRAMERATE, CONF_CONTENT_TYPE,
    CONF_STREAM_SOURCE, CONF_STILL_IMAGE_URL)

from homeassistant.helpers import config_validation as cv

from .blue_iris_api import _get_api
from .const import *
from homeassistant.components.generic.camera import GenericCamera

DEPENDENCIES = [DOMAIN]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the BlueIris Switch."""
    _LOGGER.debug(f"Starting async_setup_entry")

    api = _get_api(hass)

    if api is None:
        return

    camera_list = api.camera_list
    username = api.username
    password = api.password
    base_url = api.base_url

    image_url = f'{base_url}/image/{CAMERA_ID_PLACEHOLDER}?q=100&s=100'
    stream_url = f'{base_url}/h264/{CAMERA_ID_PLACEHOLDER}/temp.m3u8'

    entities = []
    for camera in camera_list:
        _LOGGER.debug(f"Processing new camera: {camera}")

        camera_id = camera.get("optionValue")
        camera_name = camera.get("optionDisplay")

        still_image_url = image_url.replace(CAMERA_ID_PLACEHOLDER, camera_id)
        still_image_url_template = cv.template(still_image_url)

        stream_source = stream_url.replace(CAMERA_ID_PLACEHOLDER, camera_id)

        device_info = {
            CONF_NAME: f"{DEFAULT_NAME} {camera_name}",
            CONF_STILL_IMAGE_URL: still_image_url_template,
            CONF_STREAM_SOURCE: stream_source,
            CONF_LIMIT_REFETCH_TO_URL_CHANGE: False,
            CONF_FRAMERATE: 2,
            CONF_CONTENT_TYPE: DEFAULT_CONTENT_TYPE,
            CONF_VERIFY_SSL: False,
            CONF_USERNAME: username,
            CONF_PASSWORD: password,
            CONF_AUTHENTICATION: AUTHENTICATION_BASIC
        }

        bi_camera = BlueIrisCamera(hass, device_info, api, camera)
        entities.append(bi_camera)

    async_add_devices(entities)


class BlueIrisCamera(GenericCamera):
    def __init__(self, hass, device_info, api, camera):
        """Initialize the MQTT binary sensor."""
        super().__init__(hass, device_info)

        self._api = api
        self._camera = camera

    @property
    def state_attributes(self):
        """Return the camera state attributes."""
        attrs = super().state_attributes

        for key in ATTR_BLUE_IRIS_CAMERA:
            if key in self._camera and key not in [CONF_NAME, CONF_ID]:
                key_name = ATTR_BLUE_IRIS_CAMERA[key]

                attrs[key_name] = self._camera[key]

        return attrs

