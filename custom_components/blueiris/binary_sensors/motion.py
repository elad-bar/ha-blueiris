from custom_components.blueiris import BlueIrisHomeAssistant
from .base import BlueIrisBinarySensor


class BlueIrisMotionBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, hass, ha: BlueIrisHomeAssistant, entity):
        """Initialize the MQTT binary sensor."""
        super().__init__(hass, ha, entity)
