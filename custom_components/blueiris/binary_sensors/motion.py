from .base import BlueIrisBinarySensor


class BlueIrisMotionBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, hass, integration_name, entity):
        """Initialize the MQTT binary sensor."""
        super().__init__(hass, integration_name, entity)
