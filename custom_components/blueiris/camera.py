"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/camera.blueiris/
"""
from abc import ABC
import asyncio
import logging
from typing import Optional

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.components.camera import SUPPORT_STREAM, Camera
from homeassistant.const import CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .helpers.const import *
from .models.base_entity import BlueIrisEntity, async_setup_base_entry
from .models.entity_data import EntityData

DEPENDENCIES = [DOMAIN]

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = DOMAIN_CAMERA


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the BlueIris Camera."""
    await async_setup_base_entry(
        hass, config_entry, async_add_devices, CURRENT_DOMAIN, get_camera
        )
    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
       SERVICE_TRIGGER_CAMERA,
       {},
       SERVICE_TRIGGER_CAMERA,
    )
    platform.async_register_entity_service(
       SERVICE_MOVE_TO_PRESET,
       {
           vol.Required('preset'): cv.positive_int,
       },
       SERVICE_MOVE_TO_PRESET,
    )



async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"async_unload_entry {CURRENT_DOMAIN}: {config_entry}")

    return True


def get_camera(hass: HomeAssistant, host: str, entity: EntityData):
    device_info = entity.details

    camera = BlueIrisCamera(hass, device_info)
    camera.initialize(hass, host, entity, CURRENT_DOMAIN)

    return camera


class BlueIrisCamera(Camera, BlueIrisEntity, ABC):
    """ BlueIris Camera """

    def __init__(self, hass, device_info):
        super().__init__()
        self.hass = hass

        stream_source = device_info.get(CONF_STREAM_SOURCE)
        stream_support = device_info.get(CONF_SUPPORT_STREAM, False)

        stream_support_flag = 0

        if stream_source and stream_support:
            stream_support_flag = SUPPORT_STREAM

        self._still_image_url = device_info[CONF_STILL_IMAGE_URL]
        self._still_image_url.hass = hass

        self._stream_source = device_info[CONF_STREAM_SOURCE]
        self._limit_refetch = device_info[CONF_LIMIT_REFETCH_TO_URL_CHANGE]
        self._frame_interval = 1 / device_info[CONF_FRAMERATE]
        self._supported_features = stream_support_flag
        self.content_type = device_info[CONF_CONTENT_TYPE]
        self.verify_ssl = device_info[CONF_VERIFY_SSL]

        username = device_info.get(CONF_USERNAME)
        password = device_info.get(CONF_PASSWORD)

        if username and password:
            self._auth = aiohttp.BasicAuth(username, password=password)
        else:
            self._auth = None

        self._last_url = None
        self._last_image = None


    def _immediate_update(self, previous_state: bool):
        if previous_state != self.entity.state:
            _LOGGER.debug(
                f"{self.name} updated from {previous_state} to {self.entity.state}"
            )

        super()._immediate_update(previous_state)

    async def async_added_to_hass_local(self):
        """Subscribe MQTT events."""
        _LOGGER.info(f"Added new {self.name}")

    @property
    def supported_features(self):
        """Return supported features for this camera."""
        return self._supported_features

    @property
    def frame_interval(self):
        """Return the interval between frames of the mjpeg stream."""
        return self._frame_interval

    def camera_image(self, width: Optional[int] = None, height: Optional[int] = None) -> Optional[bytes]:
        """Return bytes of camera image."""
        return asyncio.run_coroutine_threadsafe(
            self.async_camera_image(), self.hass.loop
        ).result()

    async def async_camera_image(self, width: Optional[int] = None, height: Optional[int] = None) -> Optional[bytes]:
        """Return a still image response from the camera."""
        try:
            url = self._still_image_url.async_render()
        except TemplateError as err:
            _LOGGER.error("Error parsing template %s: %s", self._still_image_url, err)
            return self._last_image

        if url == self._last_url and self._limit_refetch:
            return self._last_image

        try:
            websession = async_get_clientsession(self.hass, verify_ssl=self.verify_ssl)
            with async_timeout.timeout(10):
                response = await websession.get(url, auth=self._auth)
            self._last_image = await response.read()
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout getting camera image from %s", self.name)
            return self._last_image
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting new camera image from %s: %s", self.name, err)
            return self._last_image

        self._last_url = url
        return self._last_image

    async def stream_source(self):
        """Return the source of the stream."""
        return self._stream_source

    async def trigger_camera(self):
        if self.entity.attributes[BI_CAMERA_ATTR_GROUP_CAMERAS] == NOT_AVAILABLE:
            await self.api.trigger_camera(self.entity.id)
        else:
            for grouped_camera in self.entity.attributes[BI_CAMERA_ATTR_GROUP_CAMERAS]:
                await self.api.trigger_camera(grouped_camera)

    async def move_to_preset(self, preset):
        if self.entity.attributes[BI_CAMERA_ATTR_GROUP_CAMERAS] == NOT_AVAILABLE:
            await self.api.move_to_preset(self.entity.id, preset)
        else:
            for grouped_camera in self.entity.attributes[BI_CAMERA_ATTR_GROUP_CAMERAS]:
                await self.api.move_to_preset(grouped_camera, preset)
