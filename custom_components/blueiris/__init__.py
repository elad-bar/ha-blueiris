"""
This component provides support for Blue Iris.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/blueiris/
"""
import sys
import logging

import voluptuous as vol

from homeassistant.const import (
    CONF_ROOM, CONF_EXCLUDE, CONF_NAME, CONF_HOST, CONF_PORT, CONF_PASSWORD,
    CONF_USERNAME, CONF_SSL, CONF_ID)
from homeassistant.helpers import config_validation as cv

from .const import VERSION
from .const import *
from .blue_iris_data import BlueIrisData
from .home_assistant import BlueIrisHomeAssistant

_LOGGER = logging.getLogger(__name__)

CAMERA_SCHEMA = vol.Schema({
    vol.Required(CONF_ID): cv.string,
    vol.Optional(CONF_NAME, default=None): cv.string,
    vol.Optional(CONF_ROOM, default=None): cv.string,
})

PROFILE_SCHEMA = vol.Schema({
    vol.Required(CONF_PROFILE_ARMED): vol.All(vol.Coerce(int),
                                              vol.Range(min=-1, max=7)),
    vol.Required(CONF_PROFILE_UNARMED): vol.All(vol.Coerce(int),
                                                vol.Range(min=-1, max=7)),
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.string,
        vol.Required(CONF_CAMERAS):
            vol.All(cv.ensure_list, [vol.Any(CAMERA_SCHEMA)]),
        vol.Optional(CONF_EXCLUDE):
            vol.All(cv.ensure_list, [vol.In(SYSTEM_CAMERA_CONFIG)]),
        vol.Optional(CONF_PROFILE): PROFILE_SCHEMA,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SSL, default=False): cv.boolean,
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up a Blue Iris component."""
    ha = None
    initialized = False

    try:
        conf = config[DOMAIN]
        scan_interval = SCAN_INTERVAL
        host = conf.get(CONF_HOST)
        port = conf.get(CONF_PORT)
        cameras = conf.get(CONF_CAMERAS)
        exclude = conf.get(CONF_EXCLUDE)
        username = conf.get(CONF_USERNAME)
        password = conf.get(CONF_PASSWORD)
        ssl = conf.get(CONF_SSL)
        profile = conf.get(CONF_PROFILE)

        bi_data = BlueIrisData(host, port, cameras, username, password, ssl,
                               exclude, profile, scan_interval, cv.template)

        ha = BlueIrisHomeAssistant(hass, scan_interval, bi_data.cast_url)

        hass.data[DATA_BLUEIRIS] = bi_data

        configuration_errors = bi_data.get_configuration_errors()

        if configuration_errors is not None:
            all_errors = "<br /> - ".join(configuration_errors)
            error_message = f"<b>Errors while loading configuration:</b>" \
                f"<br />{all_errors}"

            ha.notify_error_message(error_message)
        else:
            camera_list = bi_data.get_all_cameras()

            ha.initialize(bi_data.update, camera_list)

            initialized = True

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        if ha is not None:
            ha.notify_error(ex, line_number)

    return initialized
