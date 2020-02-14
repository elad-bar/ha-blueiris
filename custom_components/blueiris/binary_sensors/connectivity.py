from homeassistant.helpers.dispatcher import async_dispatcher_connect

from custom_components.blueiris.const import *
from .base import BlueIrisBinarySensor


class BlueIrisConnectivityBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, camera, is_online):
        """Initialize the MQTT binary sensor."""
        super().__init__(camera, SENSOR_CONNECTIVITY_NAME)

        self._state = not is_online

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        state = self._state
        if self._camera_id in SYSTEM_CAMERA_ID:
            state = False

        return not state
