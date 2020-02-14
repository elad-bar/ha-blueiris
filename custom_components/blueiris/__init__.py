"""
This component provides support for Blue Iris.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/blueiris/
"""
import sys
import logging
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant

from .const import VERSION
from .const import *
from .blue_iris_api import BlueIrisApi
from .home_assistant import BlueIrisHomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Blue Iris component."""
    initialized = False

    try:
        _LOGGER.debug(f"Starting async_setup_entry of {DOMAIN}")
        bi_ha = BlueIrisHomeAssistant(hass, entry)

        hass.data[DATA_BLUEIRIS] = bi_ha

        await bi_ha.initialize()

        initialized = True

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to load BlueIris, error: {ex}, line: {line_number}")

    return initialized


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload = hass.config_entries.async_forward_entry_unload

    await hass.data[DATA_BLUEIRIS].async_remove()

    hass.async_create_task(unload(entry, DOMAIN_BINARY_SENSOR))
    hass.async_create_task(unload(entry, DOMAIN_CAMERA))
    hass.async_create_task(unload(entry, DOMAIN_SWITCH))

    del hass.data[DATA_BLUEIRIS]

    return True


async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry):
    """Triggered by config entry options updates."""
    hass.data[DATA_BLUEIRIS].options = entry.options
