import asyncio
import logging
from datetime import datetime

from custom_components.blueiris.const import *
from .base import BlueIrisBinarySensor

_LOGGER = logging.getLogger(__name__)


class BlueIrisAudioBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, camera):
        """Initialize the MQTT binary sensor."""
        super().__init__(camera, SENSOR_AUDIO_NAME)

        self._last_alert = None

    def update_data(self, event_type, trigger):
        is_trigger_off = trigger == STATE_OFF
        current_timestamp = datetime.now().timestamp()
        perform_action = True

        if is_trigger_off and \
                self._last_alert is not None and \
                current_timestamp - self._last_alert <= AUDIO_EVENT_LENGTH:

            perform_action = False

        if perform_action:
            super().update_data(event_type, trigger)

            self._last_alert = None if is_trigger_off else current_timestamp
            self.hass.async_create_task(self.turn_off_automatically(event_type))

    async def turn_off_automatically(self, event_type):
        await asyncio.sleep(AUDIO_EVENT_LENGTH)

        super().update_data(event_type, STATE_OFF)
