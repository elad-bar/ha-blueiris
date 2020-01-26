from custom_components.blueiris.const import *
from .base import BlueIrisBinarySensor


class BlueIrisMotionBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, camera):
        """Initialize the MQTT binary sensor."""
        super().__init__(camera, SENSOR_MOTION_NAME)
