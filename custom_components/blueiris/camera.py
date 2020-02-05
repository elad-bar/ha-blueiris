"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/camera.blueiris/
"""
import logging
import json

from homeassistant.const import (CONF_USERNAME, CONF_VERIFY_SSL,
                                 CONF_PASSWORD, CONF_AUTHENTICATION)
from homeassistant.components.camera import (
    DEFAULT_CONTENT_TYPE)
from homeassistant.components.generic.camera import (
    CONF_LIMIT_REFETCH_TO_URL_CHANGE, CONF_FRAMERATE, CONF_CONTENT_TYPE,
    CONF_STREAM_SOURCE, CONF_STILL_IMAGE_URL)

from homeassistant.helpers import config_validation as cv

from .const import *
from homeassistant.components.generic.camera import GenericCamera

DEPENDENCIES = [DOMAIN]

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass,
                               config,
                               async_add_entities,
                               discovery_info=None):
    """Set up a Blue Iris Camera."""
    if discovery_info is None:
        return

    camera_list = json.loads(discovery_info)

    bi_camera_list = []
    for camera_id in camera_list:
        camera = camera_list[camera_id]
        _LOGGER.info(f"Processing new camera: {camera_id}")

        still_image_url = camera.get(CONF_STILL_IMAGE_URL)
        still_image_url_template = cv.template(still_image_url)

        device_info = {
            CONF_NAME: camera.get(CONF_NAME),
            CONF_STILL_IMAGE_URL: still_image_url_template,
            CONF_STREAM_SOURCE: camera.get(CONF_STREAM_SOURCE),
            CONF_LIMIT_REFETCH_TO_URL_CHANGE: False,
            CONF_FRAMERATE: 2,
            CONF_CONTENT_TYPE: DEFAULT_CONTENT_TYPE,
            CONF_VERIFY_SSL: False,
            CONF_USERNAME: camera.get(CONF_USERNAME),
            CONF_PASSWORD: camera.get(CONF_PASSWORD),
            CONF_AUTHENTICATION: AUTHENTICATION_BASIC
        }

        _LOGGER.debug(f'Creating camera: {device_info}')

        bi_camera = GenericCamera(hass, device_info)
        bi_camera_list.append(bi_camera)

        _LOGGER.debug(f"Camera created: {bi_camera}")

    async_add_entities(bi_camera_list, True)
