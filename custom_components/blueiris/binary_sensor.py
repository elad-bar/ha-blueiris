"""
Support for Blue Iris binary sensors.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.blueiris/
"""
import logging

from .binary_sensors import get_binary_sensor
from .helpers.const import *
from .models.base_entity import async_setup_base_entry

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN, "mqtt"]

CURRENT_DOMAIN = DOMAIN_BINARY_SENSOR


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the BlueIris Binary Sensor."""
    await async_setup_base_entry(
        hass, config_entry, async_add_devices, CURRENT_DOMAIN, get_binary_sensor
    )


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"async_unload_entry {CURRENT_DOMAIN}: {config_entry}")

    return True
