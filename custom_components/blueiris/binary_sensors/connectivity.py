from custom_components.blueiris.const import *
from .base import BlueIrisBinarySensor


class BlueIrisConnectivityBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, camera):
        """Initialize the MQTT binary sensor."""
        super().__init__(camera, SENSOR_CONNECTIVITY_NAME)

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return not self._state
