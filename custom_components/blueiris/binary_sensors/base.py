"""
Support for Blue Iris binary sensors.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.blueiris/
"""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice

from ..helpers.const import *
from ..models.base_entity import BlueIrisEntity

_LOGGER = logging.getLogger(__name__)


class BlueIrisBinarySensor(BinarySensorDevice, BlueIrisEntity):
    """Representation a binary sensor that is updated by MQTT."""

    @property
    def topic(self):
        """Return the polling state."""
        return self.entity.topic

    @property
    def event_type(self):
        """Return the polling state."""
        return self.entity.event

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self.entity.state

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self.entity.device_class

    @property
    def force_update(self):
        """Force update."""
        return DEFAULT_FORCE_UPDATE
