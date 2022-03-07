import logging
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ..managers.home_assistant import BlueIrisHomeAssistant
from ..managers.password_manager import PasswordManager
from .const import *

_LOGGER = logging.getLogger(__name__)


def clear_ha(hass: HomeAssistant, entry_id):
    if DATA_BLUEIRIS not in hass.data:
        hass.data[DATA_BLUEIRIS] = dict()

    del hass.data[DATA_BLUEIRIS][entry_id]


def get_ha(hass: HomeAssistant, entry_id):
    ha_data = hass.data.get(DATA_BLUEIRIS, dict())
    ha = ha_data.get(entry_id)

    return ha


async def async_set_ha(hass: HomeAssistant, entry: ConfigEntry):
    try:
        if DATA_BLUEIRIS not in hass.data:
            hass.data[DATA_BLUEIRIS] = dict()

        if PASSWORD_MANAGER_BLUEIRIS not in hass.data:
            hass.data[PASSWORD_MANAGER_BLUEIRIS] = PasswordManager(hass)

        password_manager = hass.data[PASSWORD_MANAGER_BLUEIRIS]

        instance = BlueIrisHomeAssistant(hass, password_manager)

        await instance.async_init(entry)

        hass.data[DATA_BLUEIRIS][entry.entry_id] = instance
    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to async_set_ha, error: {ex}, line: {line_number}")


async def handle_log_level(hass: HomeAssistant, entry: ConfigEntry):
    log_level = entry.options.get(CONF_LOG_LEVEL, LOG_LEVEL_DEFAULT)

    if log_level == LOG_LEVEL_DEFAULT:
        return

    log_level_data = {f"custom_components.{DOMAIN}": log_level.lower()}

    try:
       await hass.services.async_call(DOMAIN_LOGGER, SERVICE_SET_LEVEL, log_level_data)

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to set log level. Ensure you have logging enabled in configuration.yaml., error: {ex}, line: {line_number}")
