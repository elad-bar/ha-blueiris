"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/camera.blueiris/
"""
import logging
from abc import ABC
from homeassistant.components.generic.camera import GenericCamera
from homeassistant.core import HomeAssistant

from .models.base_entity import BlueIrisEntity, async_setup_base_entry
from .helpers.const import *
from .models.entity_data import EntityData

DEPENDENCIES = [DOMAIN]

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = DOMAIN_CAMERA


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the BlueIris Camera."""
    await async_setup_base_entry(hass, config_entry, async_add_devices, CURRENT_DOMAIN, get_camera)


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"async_unload_entry {CURRENT_DOMAIN}: {config_entry}")

    return True


def get_camera(hass: HomeAssistant, host: str, entity: EntityData):
    device_info = entity.details

    camera = BlueIrisCamera(hass, device_info)
    camera.initialize(hass, host, entity, CURRENT_DOMAIN)

    return camera


class BlueIrisCamera(GenericCamera, BlueIrisEntity, ABC):
    """ BlueIris Camera """
    def __init__(self, hass, device_info):
        super().__init__(hass, device_info)

    def _immediate_update(self, previous_state: bool):
        if previous_state != self.entity.state:
            _LOGGER.debug(f"{self.name} updated from {previous_state} to {self.entity.state}")

        super()._immediate_update(previous_state)

    async def async_added_to_hass_local(self):
        """Subscribe MQTT events."""
        _LOGGER.info(f"Added new {self.name}")
