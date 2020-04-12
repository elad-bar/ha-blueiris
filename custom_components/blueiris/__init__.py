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
from .home_assistant import _async_set_ha

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Blue Iris component."""
    initialized = False

    try:
        _LOGGER.debug(f"Starting async_setup_entry of {DOMAIN}")
        entry.add_update_listener(async_options_updated)
        host = entry.data.get(CONF_HOST)

        await _async_set_ha(hass, host, entry)

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

    if ha is not None:
        await ha.async_remove()

    return True


async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry):
    """Triggered by config entry options updates."""
    _LOGGER.info(f"async_options_updated, Entry: {entry.as_dict()} ")

    host = entry.data.get(CONF_HOST)
    ha = _get_ha(hass, host)

    if ha is not None:
        await ha.async_update_entry(entry)


def _get_ha(hass, host):
    ha_data = hass.data.get(DATA_BLUEIRIS, {})
    ha = ha_data.get(host)

    return ha
