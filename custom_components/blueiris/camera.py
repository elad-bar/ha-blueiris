"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/camera.blueiris/
"""
import asyncio
import logging

import requests

from homeassistant.exceptions import TemplateError
from homeassistant.const import (CONF_NAME, CONF_USERNAME, CONF_VERIFY_SSL,
                                 CONF_PASSWORD, CONF_AUTHENTICATION)
from homeassistant.components.camera import (
    DEFAULT_CONTENT_TYPE)
from homeassistant.components.generic.camera import (
    CONF_LIMIT_REFETCH_TO_URL_CHANGE, CONF_FRAMERATE, CONF_CONTENT_TYPE,
    CONF_STREAM_SOURCE, CONF_STILL_IMAGE_URL)

from .const import *
from homeassistant.components.generic.camera import GenericCamera

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
        _LOGGER.info(f"Processing new camera: {camera_id}")

        device_info = {
            CONF_NAME: camera.get(CONF_NAME),
            CONF_STILL_IMAGE_URL: camera.get(CONF_STILL_IMAGE_URL),
            CONF_STREAM_SOURCE: camera.get(CONF_STREAM_SOURCE),
            CONF_LIMIT_REFETCH_TO_URL_CHANGE: False,
            CONF_FRAMERATE: 2,
            CONF_CONTENT_TYPE: DEFAULT_CONTENT_TYPE,
            CONF_VERIFY_SSL: False,
            CONF_USERNAME: camera.get(CONF_USERNAME),
            CONF_PASSWORD: camera.get(CONF_PASSWORD),
            CONF_AUTHENTICATION: AUTHENTICATION_BASIC
        }

        _LOGGER.info(f'Creating camera: {device_info}')

        bi_camera = BlueIrisCamera(hass, device_info)
        bi_camera_list.append(bi_camera)

        _LOGGER.info(f"Camera created: {bi_camera}")

    async_add_entities(bi_camera_list, True)


class BlueIrisCamera(GenericCamera):
    async def async_camera_image(self):
        """Return a still image response from the camera."""
        try:
            url = self._still_image_url.async_render()
        except TemplateError as err:
            _LOGGER.error("Error parsing template %s: %s", self._still_image_url, err)
            return self._last_image

        if url == self._last_url and self._limit_refetch:
            return self._last_image

        try:
            response = requests.get(
                url, timeout=10, auth=self._auth, verify=self.verify_ssl
            )
            return response.content
        except requests.exceptions.RequestException as error:
            _LOGGER.error("Error getting camera image: %s", error)
            return self._last_image

