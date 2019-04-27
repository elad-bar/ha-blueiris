"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/blueiris/
"""
import logging

from homeassistant.const import (EVENT_HOMEASSISTANT_START)
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import track_time_interval

from .const import *

_LOGGER = logging.getLogger(__name__)


class BlueIrisHomeAssistant:
    def __init__(self, hass, scan_interval):
        self._scan_interval = scan_interval
        self._hass = hass

    def initialize(self, bi_refresh_callback):
        def bi_refresh(event_time):
            """Call BlueIris to refresh information."""
            _LOGGER.debug(f"Updating {DOMAIN} component at {event_time}")
            bi_refresh_callback()
            dispatcher_send(self._hass, SIGNAL_UPDATE_BLUEIRIS)

        track_time_interval(self._hass, bi_refresh, self._scan_interval)

        self._hass.bus.listen_once(EVENT_HOMEASSISTANT_START, bi_refresh)

    def notify_error(self, ex, line_number):
        _LOGGER.error(f"Error while initializing {DOMAIN}, exception: {ex},"
                      " Line: {line_number}")

        self._hass.components.persistent_notification.create(
            f"Error: {ex}<br /> You will need to restart hass after fixing.",
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID)

    def notify_error_message(self, message):
        _LOGGER.error(f"Error while initializing {DOMAIN}, Error: {message}")

        self._hass.components.persistent_notification.create(
            (f"Error: {message}<br /> You will need to restart hass after"
             " fixing."),
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID)
