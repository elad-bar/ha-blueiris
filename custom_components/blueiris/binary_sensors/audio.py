from datetime import datetime
import logging

from homeassistant.components.binary_sensor import STATE_OFF
from homeassistant.helpers.event import async_call_later

from ..helpers.const import *
from .base import BlueIrisBinarySensor

_LOGGER = logging.getLogger(__name__)


class BlueIrisAudioBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self):
        """Initialize the MQTT binary sensor."""
        super().__init__()

        self._last_alert = None

    async def async_added_to_hass_local(self):
        """Subscribe MQTT events."""
        _LOGGER.info(f"Added new {self.name}")

    def _immediate_update(self, previous_state: bool):
        if previous_state != self.entity.state:
            _LOGGER.debug(
                f"{self.name} updated from {previous_state} to {self.entity.state}"
            )

        is_trigger_off = self.state == STATE_OFF
        current_timestamp = datetime.now().timestamp()

        def turn_off_automatically(now):
            _LOGGER.info(f"Audio alert off | {self.name} @{now}")

            self.entity_manager.set_mqtt_state(self.topic, self.event_type, False)

            self.hass.async_create_task(self.ha.async_update(None))

        if is_trigger_off:
            self._last_alert = None
            super()._immediate_update(previous_state)

        else:
            should_alert = True

            if self._last_alert is None:
                message = "Identified first time"
            else:
                time_since = current_timestamp - self._last_alert
                message = f"{time_since} seconds ago"

                if current_timestamp - self._last_alert > AUDIO_EVENT_LENGTH:
                    message = f"Identified {message}"
                else:
                    message = f"Irrelevant {message}"
                    should_alert = False

            if should_alert:
                _LOGGER.info(f"Audio alert on, {message} | {self.name}")

                self._last_alert = current_timestamp
                super()._immediate_update(previous_state)

                async_call_later(self.hass, 2, turn_off_automatically)
            else:
                _LOGGER.debug(f"Audio alert on, {message} | {self.name}")
