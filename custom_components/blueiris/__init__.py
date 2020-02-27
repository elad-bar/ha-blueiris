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
from .home_assistant import BlueIrisHomeAssistant, _get_ha

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Blue Iris component."""
    initialized = False

    try:
        _LOGGER.debug(f"Starting async_setup_entry of {DOMAIN}")
        entry.add_update_listener(async_options_updated)

        bi_ha = BlueIrisHomeAssistant(hass, entry)

        await bi_ha.initialize()

        initialized = True

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to load BlueIris, error: {ex}, line: {line_number}")

    return initialized


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    host = entry.data.get(CONF_HOST)
    ha = _get_ha(hass, host)

    await ha.async_remove()

    return True


async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry):
    """Triggered by config entry options updates."""
    host = entry.data.get(CONF_HOST)
    ha = _get_ha(hass, host)

    _LOGGER.info(f"async_options_updated {host}, Entry: {entry.as_dict()} ")

    await ha.async_update_entry(entry, True)
