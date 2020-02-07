"""
This component provides support for Blue Iris.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/blueiris/
"""
import sys
import logging
import json

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry

from homeassistant.const import (
    CONF_HOST, CONF_PORT, CONF_PASSWORD,
    CONF_USERNAME, CONF_SSL)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import VERSION
from .const import *
from .blue_iris_api import BlueIrisApi
from .home_assistant import BlueIrisHomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up a Blue Iris component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Blue Iris component."""
    ha = None
    initialized = False

    try:
        _LOGGER.debug(f"Starting async_setup_entry of {DOMAIN}")
        entry_data = entry.data

        host = entry_data.get(CONF_HOST)
        port = entry_data.get(CONF_PORT)
        username = entry_data.get(CONF_USERNAME)
        password = entry_data.get(CONF_PASSWORD)
        ssl = entry_data.get(CONF_SSL)

        bi_api = BlueIrisApi(hass, host, port, ssl, username, password)

        await bi_api.initialize()

        bi_ha = BlueIrisHomeAssistant(hass, bi_api.cast_template)

        hass.data[DATA_BLUEIRIS] = {
            DATA_BLUEIRIS_API: bi_api,
            DATA_BLUEIRIS_HA: bi_ha
        }

        async_forward_entry_setup = hass.config_entries.async_forward_entry_setup

        hass.async_create_task(async_forward_entry_setup(entry, DOMAIN_BINARY_SENSOR))
        hass.async_create_task(async_forward_entry_setup(entry, DOMAIN_CAMERA))
        hass.async_create_task(async_forward_entry_setup(entry, DOMAIN_SWITCH))

        initialized = True

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to load BlueIris, error: {ex}, line: {line_number}")

    return initialized
