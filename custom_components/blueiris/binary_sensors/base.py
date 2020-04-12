"""
Support for Blue Iris binary sensors.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.blueiris/
"""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice

from ..base_entity import BlueIrisEntity
from ..const import *

_LOGGER = logging.getLogger(__name__)


class BlueIrisBinarySensor(BinarySensorDevice, BlueIrisEntity):
    """Representation a binary sensor that is updated by MQTT."""

    @property
    def topic(self):
        """Return the polling state."""
        return self._entity.get(ENTITY_TOPIC)

    @property
    def event_type(self):
        """Return the polling state."""
        return self._entity.get(ENTITY_EVENT)

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._entity.get(ENTITY_STATE)

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self._entity.get(ENTITY_DEVICE_CLASS)

    @property
    def force_update(self):
        """Force update."""
        return DEFAULT_FORCE_UPDATE

    def is_dirty(self, updated_entity):
        previous_state = self.is_on
        current_state = updated_entity.get(ENTITY_STATE)

        is_dirty = previous_state != current_state

        return is_dirty
