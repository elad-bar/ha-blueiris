"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/camera.blueiris/
"""
import logging
from abc import ABC
from homeassistant.components.generic.camera import GenericCamera

from .base_entity import BlueIrisEntity, _async_setup_entry
from .const import *

DEPENDENCIES = [DOMAIN]

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = DOMAIN_CAMERA


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the BlueIris Camera."""
    await _async_setup_entry(hass, config_entry, async_add_devices, CURRENT_DOMAIN, get_camera)


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"async_unload_entry {CURRENT_DOMAIN}: {config_entry}")

    return True


def get_camera(hass, host, entity):
    device_info = entity.get(ENTITY_CAMERA_DETAILS)

    camera = BlueIrisCamera(hass, device_info)
    camera.initialize(hass, host, entity, CURRENT_DOMAIN)

    return camera


class BlueIrisCamera(GenericCamera, BlueIrisEntity, ABC):
    """ BlueIris Camera """
    def __init__(self, hass, device_info):
        super().__init__(hass, device_info)
